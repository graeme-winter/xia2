#!/usr/bin/env python
# Phil.py
#   Copyright (C) 2012 Diamond Light Source, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is
#   included in the root directory of this package.
#
# Phil parameter setting - to get a single place where complex parameters to
# set for individual programs can be found. Initially this will be just a
# couple for XDS.

import os
import sys

from libtbx.phil import interface
from iotbx.phil import parse

master_phil = parse("""
general
  .short_caption = "General settings"
{
  check_image_files_readable = True
    .type = bool
    .expert_level = 2
  backstop_mask = None
    .type = path
    .short_caption = "Backstop mask"
}
xds {
  z_min = 0.0
    .type = float
  delphi = 5
    .type = float
  delphi_small = 30
    .type = float
  untrusted_ellipse = None
    .type = ints(size = 4)
    .multiple = True
  untrusted_rectangle = None
    .type = ints(size = 4)
    .multiple = True
  trusted_region = None
    .type = floats(size = 2)
  profile_grid_size = None
    .type = ints(size = 2)
  keep_outliers = False
    .type = bool
    .help = "Do not remove outliers in integration and scaling"
  correct {
    refine = *DISTANCE *BEAM *AXIS *ORIENTATION *CELL *POSITION
      .type = choice(multi = True)
      .help = 'what to refine in the CORRECT step'
    air = None
      .type = float(value_min=0)
  }
  integrate {
    refine = *ORIENTATION *CELL *BEAM *DISTANCE AXIS *POSITION
      .type = choice(multi = True)
      .help = 'what to refine in first pass of integration'
    refine_final = *ORIENTATION *CELL BEAM DISTANCE AXIS POSITION
      .type = choice(multi = True)
      .help = 'what to refine in final pass of integration'
    fix_scale = False
      .type = bool
    delphi = 0
      .type = float
    reflecting_range = 0
      .type = float
    reflecting_range_esd = 0
      .type = float
    beam_divergence = 0
      .type = float
    beam_divergence_esd = 0
      .type = float
    reintegrate = true
      .type = bool
  }
  init {
    fix_scale = False
      .type = bool
  }
  defpix {
    value_range_for_trusted_detector_pixels = None
      .type = ints(size=2)
  }
  index {
    refine = *ORIENTATION *CELL *BEAM *DISTANCE *AXIS *POSITION
      .type = choice(multi = True)
      .help = 'what to refine in autoindexing'
    debug = *OFF ON
      .type = choice(multi = False)
      .help = 'output enganced debugging for indexing'
    xparm = None
      .type = path
      .help = 'Use refined GXPARM.XDS geometry in indexing'
    xparm_ub = None
      .type = path
      .help = 'Use refined GXPARM.XDS orientation matrix in indexing'
  }
  colspot {
    minimum_pixels_per_spot = 1
      .type = int
  }
  xscale {
    min_isigma = 3.0
      .type = float
    zero_dose = False
      .type = bool
      .help = "Enable XSCALE zero dose extrapolation"
  }
  merge2cbf {
    merge_n_images = 2
      .type = int(value_min=1)
      .help = "Number of input images to average into a single output image"
    data_range = None
      .type = ints(size=2, value_min=0)
    moving_average = False
      .type = bool
      .help = "If true, then perform a moving average over the sweep, i.e. given"
              "images 1, 2, 3, 4, 5, 6, ..., with averaging over three images,"
              "the output frames would cover 1-3, 2-4, 3-5, 4-6, etc."
              "Otherwise, a straight summation is performed:"
              " 1-3, 4-6, 7-9, etc."
  }
}
dials
  .short_caption = "DIALS settings"
{
  fix_geometry = False
    .type = bool
    .help = "Whether or not to refine geometry in dials.index and dials.refine."
            "Most useful when also providing a reference geometry to xia2."
    .short_caption = "Fix geometry"
    .expert_level = 1
  outlier
    .short_caption = "Centroid outlier rejection"
  {
    algorithm = null *auto mcd tukey sauter_poon
      .type = choice
      .short_caption = "Outlier rejection algorithm"
      .expert_level = 1
  }
  fast_mode = False
    .type = bool
    .help = "Set various parameters for rapid processing, compromising on quality"
    .short_caption = "Fast mode"
    .expert_level = 1
  close_to_spindle_cutoff = 0.02
    .type = float(value_min=0.0)
    .short_caption = "Closeness to the spindle cutoff for including reflections in refinement"
    .expert_level = 2
  find_spots
    .short_caption = "Spot finding"
  {
    phil_file = None
      .type = path
      .short_caption = "phil file to pass to dials.find_spots"
      .expert_level = 1
    min_spot_size = Auto
      .type = int
      .help = "The minimum number of contiguous pixels for a spot to be"
              "accepted by the filtering algorithm."
      .short_caption = "Minimum spot size"
      .expert_level = 1
    min_local = 0
      .type = int
      .help = "The minimum number of pixels under the image processing"
              "kernel that are need to do the thresholding operation."
              "Setting the value between 2 and the total number of pixels"
              "under the kernel will force the algorithm to use that number"
              "as the minimum. If the value is less than or equal to zero,"
              "then the algorithm will use all pixels under the kernel. In"
              "effect this will add a border of pixels which are always"
              "classed as background around the edge of the image and around"
              "any masked out pixels."
      .expert_level=2
    sigma_strong = None
      .type = float
      .help = "The number of standard deviations above the mean in the local"
              "area above which the pixel will be classified as strong."
      .short_caption = "Strong pixel sigma cutoff"
      .expert_level = 1
    filter_ice_rings = False
      .type = bool
      .short_caption = "Filter ice rings"
    kernel_size = 3
      .type = int
      .help = "The size of the local area around the spot in which to"
              "calculate the mean and variance. The kernel is given as a box"
      .expert_level = 1
    global_threshold = None
      .type = float
      .help = "The global threshold value. Consider all pixels less than"
              "this value to be part of the background."
      .short_caption = "Global threshold cutoff"
      .expert_level = 1
  }
  index
    .short_caption = "Indexing"
  {
    phil_file = None
      .type = path
      .short_caption = "phil file to pass to dials.index"
      .expert_level = 1
    method = fft1d *fft3d real_space_grid_search
      .type = choice
      .short_caption = "Indexing method"
    max_cell = 0.0
      .type = float
      .help = "Maximum length of candidate unit cell basis vectors (in Angstrom)."
      .short_caption = "Maximum cell length"
      .expert_level = 1
    fft3d.n_points = None
      .type = int(value_min=0)
      .short_caption = "Number of reciprocal space grid points"
      .expert_level = 2
    reflections_per_degree = 100
      .type = int
      .short_caption = "Number of reflections per degree for random subset"
      .expert_level = 1
  }
  refine
    .short_caption = "Refinement"
    .expert_level = 1
  {
    phil_file = None
      .type = path
      .short_caption = "phil file to pass to dials.refine"
    scan_static = True
      .expert_level = 2
      .type = bool
    scan_varying = True
      .type = bool
      .short_caption = "Fit a scan-varying model"
    interval_width_degrees = 36.0
      .type = float(value_min=0.)
      .help = "Width of scan between checkpoints in degrees"
      .short_caption = "Interval width between checkpoints (if scan-varying)"
    reflections_per_degree = 100
      .type = int
      .short_caption = "Number of reflections per degree for random subset"
  }
  integrate
    .expert_level = 1
    .short_caption = "Integration"
  {
    phil_file = None
      .type = path
      .short_caption = "phil file to pass to dials.integrate"
    background_outlier_algorithm = *null nsigma truncated normal tukey mosflm
      .type = choice
      .help = "Outlier rejection performed prior to background fit"
      .short_caption = "Outlier rejection method"
    background_algorithm = simple null *glm
      .type = choice
      .short_caption = "Background fit method"
    use_threading = False
      .type = bool
      .short_caption = "Use threading"
      .expert_level = 2
    include_partials = True
      .type = bool
      .help = "Include partial reflections (scaled) in output"
      .short_caption = "Include partials"
  }
}
ccp4
  .short_caption = "CCP4 data reduction options"
  .expert_level = 1
{
  reindex
    .short_caption = "reindex"
  {
    program = 'pointless'
      .type = str
  }
  aimless
    .short_caption = "aimless"
  {
    intensities = summation profile *combine
      .type = choice
    surface_tie = 0.001
      .type = float
      .short_caption = "Surface tie"
    surface_link = True
      .type = bool
      .short_caption = "Surface link"
    secondary = 6
      .type = int
      .expert_level = 2
      .short_caption = "Aimless # secondary harmonics"
  }
  pointless
    .short_caption = "pointless"
  {
    chirality = chiral nonchiral centrosymmetric
      .type = choice
  }
  truncate
    .short_caption = "truncate"
  {
    program = 'ctruncate'
      .type = str
  }
}
strategy
  .multiple = True
  .optional = False
  .short_caption = "Strategy"
  .expert_level = 1
{
  i_over_sigi = 2.0
    .type = float(value_min=0.0)
    .help = "Target <I/SigI> at highest resolution."
  minimize_total_time = False
    .type = bool
  target_resolution = None
    .type = float(value_min=0.0)
  max_total_exposure = None
    .type = float(value_min=0.0)
    .help = "maximum total exposure/measurement time, sec, default unlimited"
  anomalous = False
    .type = bool
  dose_rate = 0.0
    .type = float(value_min=0.0)
    .help = "dose rate, Gray per Second, default 0.0 - radiation damage neglected"
  shape = 1.0
    .type = float(value_min=0.0)
    .help = "shape factor, default 1, - increase for large crystal in a small beam"
  susceptibility = 1.0
    .type = float(value_min=0.0)
    .help = "increase for radiation-sensitive crystals"
  completeness = 0.99
    .type = float(value_min=0.0, value_max=1.0)
    .help = "Target completeness"
  multiplicity = None
    .type = float(value_min=0.0)
    .help = "Target multiplicity"
  phi_range = None
    .type = floats(size=2)
    .help = "Starting phi angle and total phi rotation range"
  min_oscillation_width = 0.05
    .type = float(value_min=0.0)
    .help = "Minimum rotation width per frame (degrees)"
  xml_out = None
    .type = path
    .help = "XML-formatted data stored in file"
  max_rotation_speed = None
    .type = float(value_min=0.0)
    .help = "Maximum rotation speed (deg/sec)"
  min_exposure = None
    .type = float(value_min=0.0)
    .help = "Minimum exposure per frame (sec)"
}
xia2.settings
  .short_caption = "xia2 settings"
{
  pipeline = 2d 2di 3d 3dd 3di 3dii *dials
    .short_caption = "main processing pipeline"
    .help = "Select the xia2 main processing pipeline"
            "   2d: MOSFLM, LABELIT (if installed), AIMLESS"
            "  2di: as 2d, but use 3 wedges for indexing"
            "   3d: XDS, XSCALE, LABELIT"
            "  3di: as 3d, but use 3 wedges for indexing"
            " 3dii: XDS, XSCALE, using all images for autoindexing"
            "  3dd: as 3d, but use DIALS for indexing"
            "dials: DIALS, AIMLESS"
    .type = choice
  small_molecule = False
    .type = bool
    .short_caption = "Use small molecule settings"
    .help = "Assume that the dataset comes from a"
            "chemical crystallography experiment"
    .expert_level = 1
  failover = False
    .type = bool
    .short_caption = 'Fail over gracefully'
    .help = 'If processing a sweep fails, keep going'
    .expert_level = 1
  multi_crystal = False
    .type = bool
    .short_caption = 'Settings for working with multiple crystals'
    .help = 'Settings for working with multiple crystals'
    .expert_level = 1
  interactive = False
    .type = bool
    .short_caption = 'Interactive indexing'
    .expert_level = 1
  project = 'AUTOMATIC'
    .type = str
    .help = "A name for the data processing project"
  crystal = 'DEFAULT'
    .type = str
    .help = "A name for the crystal"
  input
    .short_caption = "xia2 input settings"
  {
    atom = None
      .type = str
      .short_caption = "Heavy atom name, optional"
      .help = "Set the heavy atom name, if appropriate"
    anomalous = Auto
      .type = bool
      .short_caption = "Separate anomalous pairs in merging"
      .expert_level = 1
    working_directory = None
      .type = path
      .short_caption = "Working directory (i.e. not $CWD)"
      .expert_level = 1
    image = None
      .type = path
      .multiple = True
      .help = "image=/path/to/an/image_001.img"
      .short_caption = "Path to an image file"
      .expert_level = 1
    json = None
      .type = path
      .multiple = True
      .help = "dxtbx-format datablock.json file which can be provided as an "
              "alternative source of images header information to avoid the "
              "need to read all the image headers on start-up."
      .short_caption = "Take headers from json file"
      .expert_level = 1
    reference_geometry = None
      .type = path
      .multiple = True
      .help = "Experimental geometry from this datablock.json or "
              "experiments.json will override the geometry from the "
              "image headers."
      .short_caption = "Take experimental geometry from json file"
      .expert_level = 1
    xinfo = None
      .type = path
      .help = "Provide an xinfo file as input as alternative to directory "
              "containing image files."
      .short_caption = "Use xinfo instead of image directory"
      .expert_level = 1
    reverse_phi = False
      .type = bool
      .help = "Reverse the direction of the phi axis rotation."
      .short_caption = "Reverse rotation axis"
      .expert_level = 1
    gain = None
      .type = float
      .help = "Detector gain if using DIALS"
      .short_caption = "Detector gain"
      .expert_level = 1
    min_images = 10
      .type = int(value_min=1)
      .help = "Minimum number of matching images to include a sweep in processing."
      .short_caption = "Minimum number of matching images"
      .expert_level = 1
    min_oscillation_range = None
      .type = int(value_min=0)
      .help = "Minimum oscillation range of a sweep for inclusion in processing."
      .short_caption = "Minimum oscillation range"
      .expert_level = 1
    include scope dials.util.options.tolerance_phil_scope
    include scope dials.util.options.geometry_phil_scope
    include scope dials.util.options.format_phil_scope

  }
  sweep
    .multiple = True
    .expert_level = 2
    .short_caption = "xia2 sweep"
  {
    id = None
      .type = str
    range = None
      .type = ints(size=2)
    exclude = False
      .type = bool
  }
  scale
    .expert_level = 1
    .short_caption = "Scaling"
  {
    directory = Auto
      .type = str
      .short_caption = "xia2 scale directory"
    free_fraction = 0.05
      .type = float(value_min=0.0, value_max=1.0)
      .help = "Fraction of free reflections"
    free_total = None
      .type = int(value_min=0)
      .help = "Total number of free reflections"
    freer_file = None
      .type = path
      .help = "Copy freer flags from this file"
    reference_reflection_file = None
      .type = path
      .help = "Reference file for testing of alternative indexing schemes"
    model = *decay *modulation *absorption partiality
      .type = choice(multi=True)
      .short_caption = "Scaling models to apply"
    scales = *rotation batch
      .type = choice
      .short_caption = "Smoothed or batch scaling"
  }
  space_group = None
    .type = space_group
    .help = "Provide a target space group to the indexing program"
    .short_caption = "Space group"
  unit_cell = None
    .type = unit_cell
    .help = "Provide a target unit cell to the indexing program"
    .short_caption = "Unit cell (requires the space group to be set)"
  resolution
    .short_caption = "Resolution"
  {
    keep_all_reflections = Auto
      .type = bool
      .help = "Keep all data regardless of resolution criteria"
      .short_caption = "Keep all data (default for small molecule mode)"
    d_max = None
      .type = float(value_min=0.0)
      .help = "Low resolution cutoff."
      .short_caption = "Low resolution cutoff"
    d_min = None
      .type = float(value_min=0.0)
      .help = "High resolution cutoff."
      .short_caption = "High resolution cutoff"
    include scope xia2.Modules.Resolutionizer.phil_str
  }
  unify_setting = False
    .type = bool
    .help = "For one crystal, multiple orientations, unify U matrix"
    .short_caption = "Unify crystal orientations"
    .expert_level = 1
  beam_centre = None
    .type = floats(size=2)
    .help = "Beam centre (x,y) coordinates (mm, mm) using the Mosflm convention"
    .short_caption = "Beam centre coordinates (mm, mm) using the Mosflm convention"
  trust_beam_centre = False
    .type = bool
    .help = "Whether or not to trust the beam centre in the image header."
            "If false, then labelit.index is used to determine a better beam "
            "centre during xia2 setup phase"
    .short_caption = "Trust beam centre"
    .expert_level = 1
  wavelength_tolerance = 0.00001
    .type = float(value_min=0.0)
    .help = "Tolerance for accepting two different wavelengths as the same wavelength."
    .short_caption = "Wavelength tolerance"
    .expert_level = 1
  read_all_image_headers = True
    .type = bool
    .short_caption = "Read all image headers"
    .expert_level = 1
  detector_distance = None
    .type = float(value_min=0.0)
    .help = "Distance between sample and detector (mm)"
    .short_caption = "Detector distance"
    .expert_level = 1
  show_template = False
    .type = bool
    .short_caption = "Show template"
    .expert_level = 1
  untrusted_rectangle_indexing = None
    .type = ints(size = 4)
    .multiple = True
    .short_caption = "Untrusted rectangle for indexing"
    .expert_level = 1
  xds_cell_deviation = 0.05, 5.0
    .type = floats(size = 2)
    .short_caption = "XDS cell deviation"
    .expert_level = 1
  xds_check_cell_deviation = False
    .type = bool
    .short_caption = "Check cell deviation in XDS IDXREF"
    .expert_level = 1
  use_brehm_diederichs = False
    .type = bool
    .help = "Use the Brehm-Diederichs algorithm to resolve an indexing "
            "ambiguity."
            "See: W. Brehm and K. Diederichs, Acta Cryst. (2014). D70, 101-109."
    .short_caption = "Brehm-Diederichs"
    .expert_level = 1
  integration
    .short_caption = "Integration"
    .expert_level = 1
  {
    profile_fitting = True
      .type = bool
      .help = "Use profile fitting not summation integration, default yes"
      .short_caption = "Use profile fitting"
    exclude_ice_regions = False
      .type = bool
      .help = "Exclude measurements from regions which are typically where "
              "ice rings land"
      .short_caption = "Exclude ice regions"
  }
  developmental
    .expert_level = 2
  {
    use_dials_spotfinder = False
      .type = bool
      .help = "This feature requires the dials project to be installed, and"
              "is not currently intended for general use. Use at your peril!"
    pointless_tolerance = 0.0
      .type = float(value_min=0.0)
      .help = "Tolerance to use in POINTLESS for comparison of data sets"
    detector_id = None
      .type = str
      .help = "Override detector serial number information"
  }
  multi_sweep_indexing = Auto
    .type = bool
    .help = "Index all sweeps together rather than combining individual results"
            "(requires dials indexer)"
    .expert_level = 2
  remove_blanks = False
    .expert_level = 2
    .type = bool
  integrate_p1 = False
    .type = bool
    .short_caption = "Integrate in P1"
    .expert_level = 1
  reintegrate_correct_lattice = True
    .type = bool
    .short_caption = "Reintegrate using a corrected lattice"
    .expert_level = 1
  lattice_rejection = True
    .type = bool
    .short_caption = "Reject lattice if constraints increase RMSD"
    .expert_level = 2
  lattice_rejection_threshold = 1.5
    .type = float
    .short_caption = "Threshold for lattice rejection"
    .expert_level = 2
  xds
    .expert_level = 1
    .short_caption = "xia2 XDS settings"
  {
    geometry_x = None
      .type = path
    geometry_y = None
      .type = path
  }
  indexer = mosflm labelit labelitii xds xdsii xdssum dials
    .type = choice
    .expert_level = 2
  refiner = mosflm xds dials
    .type = choice
    .expert_level = 2
  integrater = mosflmr xdsr mosflm xds dials
    .type = choice
    .expert_level = 2
  scaler = ccp4a xdsa
    .type = choice
    .expert_level = 2
  merging_statistics
    .short_caption = "Merging statistics"
    .expert_level = 1
  {
    source = aimless *cctbx
      .type = choice
      .help = "Use AIMLESS or cctbx for calculation of merging statistics"
      .short_caption = "Software to calculate merging statistics"
    n_bins = 20
      .type = int(value_min=1)
      .short_caption = "Number of bins"
    use_internal_variance = False
      .type = bool
      .help = Use internal variance of the data in the calculation of the merged sigmas
      .short_caption = "Use internal variance"
    eliminate_sys_absent = False
      .type = bool
      .help = Eliminate systematically absent reflections before computation of merging statistics.
      .short_caption = "Eliminate systematic absences before calculation"
  }
  verbose = False
    .type = bool
    .expert_level = 1
  multiprocessing
    .short_caption = "Multiprocessing"
    .expert_level = 1
  {
    mode = *serial parallel
      .type = choice
      .help = "Whether to process each sweep in serial (using n processes per"
              " sweep) or to process sweeps in parallel (using 1 process per"
              " sweep)."
    nproc = Auto
      .type = int(value_min=1)
      .help = "The number of processors to use per job."
    njob = Auto
      .type = int(value_min=1)
      .help = "The number of sweeps to process simultaneously."
    type = *simple qsub
      .type = choice
      .help = "How to run the parallel processing jobs, e.g. over a cluster"
    qsub_command = ''
      .type = str
      .help = "The command to use to submit qsub jobs"
  }
}
""", process_includes=True)

PhilIndex = interface.index(master_phil=master_phil)

if __name__ == '__main__':
  PhilIndex.working_phil.show()
