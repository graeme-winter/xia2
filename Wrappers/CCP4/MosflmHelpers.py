#!/usr/bin/env python
# MosflmHelpers.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
#
# 23rd June 2006
# 
# Helper functions which will make working with Mosflm in detail a little
# easier... for instance parsing the rather extensive output file to 
# decide if the integration went well or no.
# 
# FIXME 19/OCT/06 need to be able to parse the integration log to be able to 
#                 decide if it went ok for all images.
# 
# FIXME 19/OCT/06 would also be useful to be able to get an estimate of
#                 the "useful" integration limit (e.g. where the individual
#                 reflections have an I/sigma ~ 1)

import os
import sys
import math

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'

if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.environ['XIA2_ROOT'])

# output streams

from Handlers.Streams import Admin, Science, Status, Chatter

def detector_class_to_mosflm(detector_class):
    '''Get the mosflm detector type from the detector class.'''

    if 'adsc' in detector_class:
        return 'adsc'
    if 'mar' in detector_class and 'ccd' in detector_class:
        return 'marccd'
    if 'mar' in detector_class:
        return 'mar'
    if 'pilatus' in detector_class:
        return 'pilatus'
    if 'raxis' in detector_class:
        return 'raxis4'
    if 'saturn' in detector_class:
        return 'saturn'

    raise RuntimeError, 'unknown detector class "%s"' % detector_class

def _resolution_estimate(ordered_pair_list, cutoff):
    '''Come up with a linearly interpolated estimate of resolution at
    cutoff cutoff from input data [(resolution, i_sigma)].'''

    x = []
    y = []

    for o in ordered_pair_list:
        x.append(o[0])
        y.append(o[1])

    if max(y) < cutoff:
        # there is no point where this exceeds the resolution
        # cutoff
        return -1.0

    # this means that there is a place where the resolution cutof
    # can be reached - get there by working backwards

    x.reverse()
    y.reverse()

    if y[0] >= cutoff:
        # this exceeds the resolution limit requested
        return x[0]

    j = 0
    while y[j] < cutoff:
        j += 1

    resolution = x[j] + (cutoff - y[j]) * (x[j - 1] - x[j]) / \
                 (y[j - 1] - y[j])

    return resolution

def _parse_mosflm_integration_output(integration_output_list):
    '''Parse mosflm output from integration, passed in as a list of
    strings.'''

    length = len(integration_output_list)

    per_image_stats = {0:{}}

    current_image = 0

    pixel_size = 0.0

    for i in range(length):
        record = integration_output_list[i]
        
        if 'Pixel size of' in record:
            pixel_size = float(record.replace('mm', ' ').split()[3])

        if 'Pixel size in the' in record:
            pixel_size = float(record.replace('mm', ' ').split()[-1])
        
        if 'Processing Image' in record:
            current_image = int(record.split()[2])

            if not per_image_stats.has_key(current_image):
                per_image_stats[current_image] = {'scale':1.0}

        if 'Integrating Image' in record:
            current_image = int(record.split()[2])

        if 'XCEN    YCEN  XTOFRA   XTOFD' in record:
            data = map(float, integration_output_list[i + 1].split())
            beam = (data[0], data[1])
            distance = data[3]

            per_image_stats[current_image]['beam'] = beam
            per_image_stats[current_image]['distance'] = distance

        if 'Smoothed value for refined mosaic spread' in record:
            mosaic = float(record.split()[-1])
            per_image_stats[current_image]['mosaic'] = mosaic

        if 'Final rms residual:' in record:
            residual = float(record.replace('mm', ' ').split()[3])
            # FIXME to do this need to be able to compute the
            # residual in pixels...
            rmsd = residual / pixel_size
            per_image_stats[current_image]['rmsd_pixel'] = rmsd
            per_image_stats[current_image]['rmsd_phi'] = 0.0
            weighted_residual = float(record.split()[-1])
            per_image_stats[current_image][
                'weighted_residual'] = weighted_residual

        if 'Real cell parameters' in record:
            cell = map(float, integration_output_list[i + 1].split())
            per_image_stats[current_image]['cell'] = cell

        if 'Spots measured on this image' in record:
            spots = int(record.split()[0])
            # FIXME this is misnamed because it matches a name in the
            # XDS version of this parser.
            per_image_stats[current_image]['strong'] = spots

        if 'are OVERLOADS' in record:
            overloads = int(record.replace(',', ' ').split()[4])
            per_image_stats[current_image]['overloads'] = overloads
            
        if 'Number of bad spots' in record:
            bad = int(record.replace('=', '').split()[-1])
            # FIXME also with the name...
            per_image_stats[current_image]['rejected'] = bad

        if 'Analysis as a function of resolution.' in record and \
           'Maximum Intensity' in integration_output_list[i - 3]:
            # then get out the resolution information, spot counts and
            # so on, and generate some kind of resolution estimate
            # from this...
            # 
            # (1) compute I/sigma vs. resolution curve
            # (2) analyse to find where I/sigma gets to 1.0
            #
            # report this as a sensible resolution limit for that image
            # these will be collated in some mysterious way to give an
            # appropriate resolution limit to integrate the data set to.

            resolution = map(
                float,
                integration_output_list[i + 1].split(
                )[2:-1])
            number_full = map(
                int,
                integration_output_list[i + 3].replace('Number', '').split(
                )[:-1])
            sigma_full = map(
                float,
                integration_output_list[i + 6].replace('<I/sigma>', '').split(
                )[:-1])
            number_partial = map(
                int,
                integration_output_list[i + 8].replace('Number', '').split(
                )[:-1])
            sigma_partial = map(
                float,
                integration_output_list[i + 11].replace('<I/sigma>', '').split(
                )[:-1])

            resolution_list = []

            for j in range(len(resolution)):
                if (number_full[j] + number_partial[j]):
                    sigma = (number_full[j] * sigma_full[j] +
                             number_partial[j] * sigma_partial[j]) / \
                             (number_full[j] + number_partial[j])
                else:
                    sigma = 0.0
                resolution_list.append((resolution[j], sigma))

            # this was 1.0 - lowering for testing with broader resolution
            # limit tests...
            resolution = _resolution_estimate(resolution_list, 0.5)
            
            per_image_stats[current_image]['resolution'] = resolution
            
    per_image_stats.pop(0, None)
            
    return per_image_stats

def _print_integrate_lp(integrate_lp_stats):
    '''Print the contents of the integrate.lp dictionary.'''

    images = integrate_lp_stats.keys()
    images.sort()

    for i in images:
        data = integrate_lp_stats[i]
        print '%4d %5.3f %5d %5d %5d %4.2f %6.2f %5.2f' % \
              (i, data['scale'], data['strong'],
               data['overloads'], data['rejected'],
               data.get('mosaic', 0.0), data['distance'],
               data['resolution'])

def _happy_integrate_lp(integrate_lp_stats):
    '''Return a string which explains how happy we are with the integration.'''

    images = integrate_lp_stats.keys()
    images.sort()

    results = ''

    Science.write('Report on images %d to %d' % (min(images), max(images)),
                  forward = False)

    max_weighted_residual = 0.0

    for i in images:
        data = integrate_lp_stats[i]

        # FIXME need to look for "blank" "many bad spots" "overloaded"

        if not data.has_key('weighted_residual'):
            pass
        elif data['weighted_residual'] < max_weighted_residual:
            max_weighted_residual = data['weighted_residual']

        if not data.has_key('rmsd_pixel'):
            status = '@'
            Science.write('Image %4d ... abandoned processing',
                          forward = False)
        elif data['rmsd_pixel'] > 2.5:
            status = '!'
            Science.write('Image %4d ... very high rmsd (%f)' % \
                          (i, data['rmsd_pixel']), forward = False)
        elif data['rmsd_pixel'] > 1.0:
            status = '%'
            Science.write('Image %4d ... high rmsd (%f)' % \
                          (i, data['rmsd_pixel']), forward = False)
        else:
            status = 'o'
            Science.write('Image %4d ... ok' % i, forward = False)

        # also - # bad O overloaded . blank ! problem ? other
        # @ ABANDONED PROCESSING

        results += status

    return results

def decide_integration_resolution_limit(mosflm_integration_output):
    '''Define the resolution limit for integration, where I/sigma
    for individual reflections is about 1.0.'''

    stats = _parse_mosflm_integration_output(mosflm_integration_output)

    resolutions = []

    for k in stats.keys():
        resol = stats[k].get('resolution', -1.0)
        if resol > 0.0:
            resolutions.append(resol)

    return min(resolutions)

def _parse_mosflm_index_output(index_output_list):
    '''Parse the output text from autoindexing to build up a picture
    of the solutions.'''

    collect_solutions = False

    solutions = { }

    correct_number = 0

    for i in range(len(index_output_list)):
        output = index_output_list[i]

        if 'No PENALTY SDCELL' in output:
            collect_solutions = not collect_solutions

        if collect_solutions:
            try:
                number = int(output.split()[0])
                solutions[number] = output[:-1]
            except:
                pass

        # this will not be in the file if Mosflm doesn't think you have
        # the right answer (and often it doesn't have a clue...)
        # FIXME this sometimes has "transformed from" following...        
        if 'Suggested Solution' in output:
            correct_number = int(output.split()[2])

        # this will at least be there! - unless the input solution has
        # been set...
        if 'Mosflm has chosen solution' in output:
            correct_number = int(output.split()[4])

        if 'Solution' in output and \
               'has been chosen from the list' in output:
            correct_number = int(output.split()[1])


    if correct_number == 0:
        # cannot find what Mosflm considers the correct answer
        raise RuntimeError, 'cannot determine correct answer'

    keys = solutions.keys()
    keys.sort()

    solutions_by_lattice = { }
    
    # FIXME 25/OCT/06 also need to take the penalty into account slightly
    # because this goes very wrong for TS02/PEAK - add this to the rms
    # times a small magic number (0.5% at the moment)

    acceptable_rms = 0.0
    
    for k in keys:
        if not 'unrefined' in solutions[k]:
            list = solutions[k].split()
            penalty = float(list[1])
            number = int(list[0])
            rms = float(list[2]) + 0.005 * penalty
            latt = list[4]
            frc = float(list[3])
            cell = map(float, list[5:11])

            # decide what we consider a reasonable rms deviation
            if number == correct_number:
                acceptable_rms = 1.1 * rms

            if solutions_by_lattice.has_key(latt):
                if solutions_by_lattice[latt]['rms'] <= rms:
                    continue
                
            solutions_by_lattice[latt] = {'rms':rms,
                                          'cell':cell,
                                          'frc':frc,
                                          'number':number}
                
    # find what we think is an acceptable solution... this now moved above
    # acceptable_rms = 0.0

    # for k in solutions_by_lattice.keys():
    # if solutions_by_lattice[k]['number'] == correct_number:
    # acceptable_rms = 1.1 * solutions_by_lattice[k]['rms']

    # this should raise a HorribleIndexingException or something

    if acceptable_rms == 0.0:
        raise RuntimeError, 'something horribly bad has happened in indexing'

    # then print those which should be ok...

    results = { }
    
    lattice_to_spacegroup = {'aP':1,
                             'mP':3,
                             'mC':5,
                             'oP':16,
                             'oC':20,
                             'oF':22,
                             'oI':23,
                             'tP':75,
                             'tI':79,
                             'hP':143,
                             'hR':146,
                             'cP':195,
                             'cF':196,
                             'cI':197}
                
    for k in solutions_by_lattice.keys():
        if solutions_by_lattice[k]['rms'] < acceptable_rms:
            cell = solutions_by_lattice[k]['cell']

            # record this only if it is a standard setting!
            if k in lattice_to_spacegroup.keys():
                results[k] = {'cell':cell,
                              'goodness':solutions_by_lattice[k]['rms']}

    return results

def _parse_mosflm_index_output_all(index_output_list):
    '''Parse the output text from autoindexing to build up complete list
    of the solutions.'''

    collect_solutions = False

    solutions = { }

    for i in range(len(index_output_list)):
        output = index_output_list[i]

        if 'No PENALTY SDCELL' in output:
            collect_solutions = not collect_solutions

        if collect_solutions:
            try:
                number = int(output.split()[0])
                solutions[number] = output[:-1]
            except:
                pass

    keys = solutions.keys()
    keys.sort()

    results = { }

    for k in keys:
        if not 'unrefined' in solutions[k]:
            list = solutions[k].split()
            penalty = float(list[1])
            number = int(list[0])
            rms = float(list[2]) + 0.005 * penalty
            latt = list[4]
            frc = float(list[3])
            cell = map(float, list[5:11])
            results[k] = {'rms':rms,
                          'cell':cell,
                          'frc':frc,
                          'number':number,
                          'lattice':latt,
                          'penalty':penalty}

    return results

def _get_indexing_solution_number(index_output_list,
                                  target_cell,
                                  target_lattice):
    '''Given a list of autoindexing solutions, return the solution
    number for the provided unit cell and lattice.'''

    # get the indexing results from the standard output
    all_autoindex_results = _parse_mosflm_index_output_all(index_output_list)

    # then select the one closest to the target cell - recording the
    # solution number
    
    best = 0
    difference = 60.0

    for k in all_autoindex_results.keys():
        if all_autoindex_results[k]['lattice'] == target_lattice:
            cell = all_autoindex_results[k]['cell']
            diff = 0.0
            for j in range(6):
                diff += math.fabs(cell[j] - target_cell[j])
            if diff < difference:
                best = k
                difference = diff

    # return the solution number

    return best

def standard_mask(detector):
    '''Return a list of standard mask commands for the given detector.'''

    # ADSC Q210 2x2 binned

    if 'adsc q210' in detector:
        return ['LIMITS EXCLUDE 104.6 0.1 105.1 209.0',
                'LIMITS EXCLUDE 0.1 104.6 209.0 105.1']

    if 'adsc q315' in detector:
        return ['LIMITS EXCLUDE 104.6 0.1 105.1 314.0',
                'LIMITS EXCLUDE 209.4 0.1 210.0 314.0',
                'LIMITS EXCLUDE 0.1 104.6 314.0 105.1',
                'LIMITS EXCLUDE 0.1 209.4 314.0 210.0']
    
    # unknown detector
    
    return []
        

if __name__ == '__main__':
    integrate_lp = os.path.join(os.environ['XIA2_ROOT'], 'Wrappers', 'CCP4',
                                'Doc', 'mosflm-reintegration.log')
    stats = _parse_mosflm_integration_output(
        open(integrate_lp, 'r').readlines())
    _print_integrate_lp(stats)
    
    print _happy_integrate_lp(stats)

    print 'Integration resolution limit: %5.2fA' % \
          decide_integration_resolution_limit(
        open(integrate_lp, 'r').readlines())        

    index_lp = os.path.join(os.environ['XIA2_ROOT'], 'Wrappers', 'CCP4',
                            'Doc', 'mosflm-autoindex.log')
    _parse_mosflm_index_output(open(index_lp, 'r').readlines())
    idx = _parse_mosflm_index_output_all(open(index_lp, 'r').readlines())

    keys = idx.keys()
    keys.sort()
    for k in keys:
        print idx[k]

    target_cell = [227.0, 52.2, 43.9, 90.0, 99.0, 90.0]
    target_lattice = 'mC'

    print _get_indexing_solution_number(open(index_lp, 'r').readlines(),
                                        target_cell, target_lattice)
