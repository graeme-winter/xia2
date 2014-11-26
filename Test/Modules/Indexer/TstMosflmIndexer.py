import os
import sys
if not os.environ.has_key('XIA2CORE_ROOT'):
  raise RuntimeError, 'XIA2CORE_ROOT not defined'

if not os.environ.has_key('XIA2_ROOT'):
  raise RuntimeError, 'XIA2_ROOT not defined'

if not os.path.join(os.environ['XIA2CORE_ROOT'],
                    'Python') in sys.path:
  sys.path.append(os.path.join(os.environ['XIA2CORE_ROOT'],
                               'Python'))

if not os.environ['XIA2_ROOT'] in sys.path:
  sys.path.append(os.environ['XIA2_ROOT'])

import libtbx.load_env
from libtbx import easy_run
from libtbx.test_utils import approx_equal, open_tmp_directory, show_diff

try:
  dials_regression = libtbx.env.dist_path('dials_regression')
  have_dials_regression = True
except KeyError, e:
  have_dials_regression = False


def exercise_mosflm_indexer():
  if not have_dials_regression:
    print "Skipping exercise_mosflm_indexer(): dials_regression not configured"
    return

  xia2_demo_data = os.path.join(dials_regression, "xia2_demo_data")
  template = os.path.join(xia2_demo_data, "insulin_1_%03i.img")

  cwd = os.path.abspath(os.curdir)
  tmp_dir = os.path.abspath(open_tmp_directory())
  os.chdir(tmp_dir)

  from Modules.Indexer.MosflmIndexer import MosflmIndexer
  indexer = MosflmIndexer()
  indexer.set_working_directory(tmp_dir)
  indexer.setup_from_image(template %1)

  indexer.index()

  assert approx_equal(indexer.get_indexer_cell(),
                      (78.6657, 78.6657, 78.6657, 90.0, 90.0, 90.0), eps=1e-4)
  experiment = indexer.get_indexer_experiment_list()[0]
  sgi = experiment.crystal.get_space_group().info()
  assert sgi.type().number() == 197

  beam_centre = indexer.get_indexer_beam_centre()
  assert approx_equal(beam_centre, (94.34, 94.57), eps=1e-2)
  assert indexer.get_indexer_images() == [(1, 1), (22, 22), (45, 45)]
  print indexer.get_indexer_experiment_list()[0].crystal
  print indexer.get_indexer_experiment_list()[0].detector

  # test serialization of indexer
  json_str = indexer.as_json()
  print json_str
  indexer2 = MosflmIndexer.from_json(string=json_str)
  indexer2.index()

  assert approx_equal(indexer.get_indexer_cell(), indexer2.get_indexer_cell())
  assert approx_equal(
    indexer.get_indexer_beam_centre(), indexer2.get_indexer_beam_centre())
  assert approx_equal(
    indexer.get_indexer_images(), indexer2.get_indexer_images())

  indexer.eliminate()
  indexer2.eliminate()

  assert approx_equal(indexer.get_indexer_cell(), indexer2.get_indexer_cell())
  assert indexer.get_indexer_lattice() == 'hR'
  assert indexer2.get_indexer_lattice() == 'hR'


def run():
  exercise_mosflm_indexer()
  print "OK"


if __name__ == '__main__':
  run()