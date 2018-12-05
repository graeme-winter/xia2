# -*- coding: utf-8 -*-
#!/usr/bin/env xia2.python
from __future__ import absolute_import, division, print_function

from collections import OrderedDict
import logging


from libtbx.utils import Sorry
import iotbx.phil

from dials.array_family import flex
from dials.util.options import OptionParser
from dials.util import log
from dials.util.options import flatten_experiments, flatten_reflections
from dials.util.multi_dataset_handling import parse_multiple_datasets
from xia2.lib.bits import auto_logfiler

logger = logging.getLogger('xia2.multi_crystal_analysis')

help_message = '''
'''

phil_scope = iotbx.phil.parse('''
include scope xia2.command_line.report.phil_scope
output {
  log = xia2.multi_crystal_analysis.log
    .type = str
  debug_log = xia2.multi_crystal_analysis.debug.log
    .type = str
}
''', process_includes=True)

# local overrides for refiner.phil_scope
phil_overrides = iotbx.phil.parse('''
prefix = xia2-multi-crystal
''')

phil_scope = phil_scope.fetch(sources=[phil_overrides])

import json
from xia2.XIA2Version import Version
from xia2.command_line.report import xia2_report_base
from xia2.Modules.MultiCrystalAnalysis import batch_phil_scope
from xia2.Modules.MultiCrystal.ScaleAndMerge import DataManager
from libtbx import phil

class multi_crystal_analysis(xia2_report_base):
  def __init__(self, experiments, reflections, params):
    super(multi_crystal_analysis, self).__init__(params)
    self._data_manager = DataManager(experiments, reflections)
    self._intensities_separate = self._data_manager.reflections_as_miller_arrays(
      intensity_key='intensity.scale.value', return_batches=True)
    self.intensities = self._intensities_separate[0][0].deep_copy()
    self.batches = self._intensities_separate[0][1].deep_copy()
    for intensities, batches in self._intensities_separate[1:]:
      self.intensities = self.intensities.concatenate(intensities)
      self.batches = self.batches.concatenate(batches)

    self.params.batch = []
    scope = phil.parse(batch_phil_scope)
    for expt in self._data_manager.experiments:
      batch_params = scope.extract().batch[0]
      batch_params.id = expt.identifier
      batch_params.range = expt.scan.get_batch_range()
      self.params.batch.append(batch_params)

    self.intensities.set_observation_type_xray_intensity()
    self.report()

  @staticmethod
  def stereographic_projections(experiments_filename):
    from xia2.Wrappers.Dials.StereographicProjection import StereographicProjection
    sp_json_files = {}
    for hkl in ((1,0,0), (0,1,0), (0,0,1)):
      sp = StereographicProjection()
      auto_logfiler(sp)
      sp.add_experiments(experiments_filename)
      sp.set_hkl(hkl)
      sp.run()
      sp_json_files[hkl] = sp.get_json_filename()
    return sp_json_files

  def radiation_damage_analysis(self):
    from xia2.Modules.PyChef import Statistics

    miller_arrays = self._data_manager.reflections_as_miller_arrays(
      return_batches=True)
    for i, (intensities, batches) in enumerate(miller_arrays):
      # convert batches to dose
      data = batches.data() - self._data_manager.experiments[i].scan.get_batch_offset()
      miller_arrays[i][1] = batches.array(data=data).set_info(batches.info())
    intensities, dose = miller_arrays[0]
    for (i, d) in miller_arrays[1:]:
      intensities = intensities.concatenate(i, assert_is_similar_symmetry=False)
      dose = dose.concatenate(d, assert_is_similar_symmetry=False)

    stats = Statistics(intensities, dose.data())

    logger.debug(stats.completeness_vs_dose_str())
    logger.debug(stats.rcp_vs_dose_str())
    logger.debug(stats.scp_vs_dose_str())
    logger.debug(stats.rd_vs_dose_str())

    with open('chef.json', 'wb') as f:
      import json
      json.dump(stats.to_dict(), f)

    self._chef_stats = stats
    return stats

  def cluster_analysis(self):
    from xia2.Modules.MultiCrystal import multi_crystal_analysis
    labels = self._data_manager.experiments.identifiers()
    intensities = [i[0] for i in self._intensities_separate]
    mca = multi_crystal_analysis(
      intensities,
      labels=labels,
      prefix=None
    )

    self._cc_cluster_json = mca.to_plotly_json(
      mca.cc_matrix, mca.cc_linkage_matrix,
      labels=labels)
    self._cc_cluster_table = mca.as_table(mca.cc_clusters)

    self._cos_angle_cluster_json = mca.to_plotly_json(
      mca.cos_angle_matrix, mca.cos_angle_linkage_matrix,
      labels=labels)
    self._cos_angle_cluster_table = mca.as_table(mca.cos_angle_clusters)

    return mca

  def unit_cell_analysis(self):
    from dials.command_line.unit_cell_histogram import uc_params_from_experiments, \
      panel_distances_from_experiments, outlier_selection
    experiments = self._data_manager.experiments
    uc_params = uc_params_from_experiments(experiments)
    panel_distances = panel_distances_from_experiments(experiments)
    outliers = outlier_selection(uc_params)

    d = {}
    d.update(
      self._plot_uc_histograms(uc_params, outliers,
        #params.steps_per_angstrom
    ))
    #self._plot_uc_vs_detector_distance(uc_params, panel_distances, outliers, params.steps_per_angstrom)
    #self._plot_number_of_crystals(experiments)
    return d

  @staticmethod
  def _plot_uc_histograms(uc_params, outliers, steps_per_angstrom=20):
    uc_labels = ['a', 'b', 'c']
    a, b, c = uc_params[:3]
    d = OrderedDict()

    def uc_param_hist1d(p, l):
      nbins = 100
      return {
        'uc_hist_%s' % l: {
          'data': [{
            'x': list(p),
            'type': 'histogram',
            'connectgaps': False,
            'name': 'unit_cell_hist_%s' % l,
            'nbins': 'auto',
          }],
          'layout': {
            'title': 'Histogram of unit cell parameters',
            'xaxis': {
              'domain': [0, 0.85],
              'title': '%s (Å)' % l,
            },
            'yaxis': {
              'title': 'Frequency',
            },
            'width': 500,
            'height': 450,
          },
        },
      }

    def uc_param_hist2d(p1, p2, l1, l2):
      nbins = 100
      return {
        'uc_hist_%s_%s' % (l1, l2): {
          'data': [{
            'x': list(p1),
            'y': list(p2),
            'type': 'histogram2d',
            'connectgaps': False,
            'name': 'unit_cell_hist_%s_%s' % (l1, l2),
            'nbinsx': nbins,
            'nbinsy': nbins,
            'colorscale': 'Jet',
            'showscale': False,
          }],
          'layout': {
            'title': 'Histogram of unit cell parameters',
            'xaxis': {
              'domain': [0, 0.85],
              'title': '%s (Å)' % l1,
            },
            'yaxis': {
              'title': '%s (Å)' % l2,
            },
            'width': 500,
            'height': 450,
          },
        },
      }

    d.update(uc_param_hist1d(a, 'a'))
    d.update(uc_param_hist1d(b, 'b'))
    d.update(uc_param_hist1d(c, 'c'))

    d.update(uc_param_hist2d(a, b, 'a', 'b'))
    d.update(uc_param_hist2d(b, c, 'b', 'c'))
    d.update(uc_param_hist2d(c, a, 'c', 'a'))

    return d

  def report(self):
    super(multi_crystal_analysis, self).report()

    unit_cell_graphs = self.unit_cell_analysis()
    self.radiation_damage_analysis()
    self._cluster_analysis = self.cluster_analysis()

    overall_stats_table = self.overall_statistics_table()
    merging_stats_table = self.merging_statistics_table()
    symmetry_table_html = self.symmetry_table_html()

    json_data = {}
    json_data.update(self.multiplicity_vs_resolution_plot())
    json_data.update(self.multiplicity_histogram())
    json_data.update(self.completeness_plot())
    json_data.update(self.scale_rmerge_vs_batch_plot())
    json_data.update(self.cc_one_half_plot())
    json_data.update(self.i_over_sig_i_plot())
    json_data.update(self.i_over_sig_i_vs_batch_plot())
    json_data.update(self.second_moments_plot())
    json_data.update(self.cumulative_intensity_distribution_plot())
    json_data.update(self.l_test_plot())
    json_data.update(self.wilson_plot())
    json_data.update(self._chef_stats.to_dict())
    json_data.update(unit_cell_graphs)

    #return

    self._data_manager.export_experiments('tmp_experiments.json')
    self._stereographic_projection_files = self.stereographic_projections(
      'tmp_experiments.json')

    styles = {}
    for hkl in ((1,0,0), (0,1,0), (0,0,1)):
      with open(self._stereographic_projection_files[hkl], 'rb') as f:
        d = json.load(f)
        d['layout']['title'] = 'Stereographic projection (hkl=%i%i%i)' %hkl
        key = 'stereographic_projection_%s%s%s' %hkl
        json_data[key] = d
        styles[key] = 'square-plot'

    resolution_graphs = OrderedDict(
      (k, json_data[k]) for k in
      ('cc_one_half', 'i_over_sig_i', 'second_moments', 'wilson_intensity_plot',
       'completeness', 'multiplicity_vs_resolution') if k in json_data)

    batch_graphs = OrderedDict(
      (k, json_data[k]) for k in
      ('scale_rmerge_vs_batch', 'i_over_sig_i_vs_batch', 'completeness_vs_dose',
       'rcp_vs_dose', 'scp_vs_dose', 'rd_vs_batch_difference'))

    misc_graphs = OrderedDict(
      (k, json_data[k]) for k in
      ('cumulative_intensity_distribution', 'l_test', 'multiplicities',
       ) if k in json_data)

    for k, v in self.multiplicity_plots().iteritems():
      misc_graphs[k] = {'img': v}

    for k in ('stereographic_projection_100', 'stereographic_projection_010',
              'stereographic_projection_001'):
      misc_graphs[k] = json_data[k]

    for axis in ('h', 'k', 'l'):
      styles['multiplicity_%s' %axis] = 'square-plot'

    from jinja2 import Environment, ChoiceLoader, PackageLoader
    loader = ChoiceLoader([PackageLoader('xia2', 'templates'),
                           PackageLoader('dials', 'templates')])
    env = Environment(loader=loader)

    template = env.get_template('multi_crystal.html')
    html = template.render(
      page_title=self.params.title,
      #filename=os.path.abspath(unmerged_mtz),
      space_group=self.intensities.space_group_info().symbol_and_number(),
      unit_cell=str(self.intensities.unit_cell()),
      #mtz_history=[h.strip() for h in report.mtz_object.history()],
      overall_stats_table=overall_stats_table,
      merging_stats_table=merging_stats_table,
      cc_half_significance_level=self.params.cc_half_significance_level,
      resolution_graphs=resolution_graphs,
      batch_graphs=batch_graphs,
      misc_graphs=misc_graphs,
      unit_cell_graphs=unit_cell_graphs,
      cc_cluster_table=self._cc_cluster_table,
      cc_cluster_json=self._cc_cluster_json,
      cos_angle_cluster_table=self._cos_angle_cluster_table,
      cos_angle_cluster_json=self._cos_angle_cluster_json,
      styles=styles,
      xia2_version=Version,
    )

    with open('%s-report.json' % self.params.prefix, 'wb') as f:
      json.dump(json_data, f)

    with open('%s-report.html' % self.params.prefix, 'wb') as f:
      f.write(html.encode('ascii', 'xmlcharrefreplace'))

def run():

  # The script usage
  usage  = "usage: xia2.multi_crystal_analysis [options] [param.phil] " \
           "experiments.json reflections.pickle"

  # Create the parser
  parser = OptionParser(
    usage=usage,
    phil=phil_scope,
    read_reflections=True,
    read_experiments=True,
    check_format=False,
    epilog=help_message)

  # Parse the command line
  params, options = parser.parse_args(show_diff_phil=False)

  # Configure the logging

  for name in ('xia2', 'dials'):
    log.config(
      info=params.output.log,
      debug=params.output.debug_log,
      name=name)
  from dials.util.version import dials_version
  logger.info(dials_version())

  # Log the diff phil
  diff_phil = parser.diff_phil.as_str()
  if diff_phil is not '':
    logger.info('The following parameters have been modified:\n')
    logger.info(diff_phil)

  # Try to load the models and data
  if len(params.input.experiments) == 0:
    logger.info("No Experiments found in the input")
    parser.print_help()
    return
  if len(params.input.reflections) == 0:
    logger.info("No reflection data found in the input")
    parser.print_help()
    return
  try:
    assert len(params.input.reflections) == len(params.input.experiments)
  except AssertionError:
    raise Sorry("The number of input reflections files does not match the "
      "number of input experiments")

  expt_filenames = OrderedDict((e.filename, e.data) for e in params.input.experiments)
  refl_filenames = OrderedDict((r.filename, r.data) for r in params.input.reflections)

  experiments = flatten_experiments(params.input.experiments)
  reflections = flatten_reflections(params.input.reflections)
  reflections = parse_multiple_datasets(reflections)

  joint_table = flex.reflection_table()
  for i in range(len(reflections)):
    joint_table.extend(reflections[i])
  reflections = joint_table

  multi_crystal_analysis(experiments, reflections, params)

if __name__ == '__main__':
  run()
