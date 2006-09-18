#!/usr/bin/env python
# LabelitMosflmScript.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the terms and conditions of the
#   CCP4 Program Suite Licence Agreement as a CCP4 Library.
#   A copy of the CCP4 licence can be obtained by writing to the
#   CCP4 Secretary, Daresbury Laboratory, Warrington WA4 4AD, UK.
#
# 18th July 2006
# 
# An interface to the labelit program labelit.mosflm_script, used for
# generating an integration script for Mosflm. In this case this is used
# for generating the matrix file to make mosflm work. This will be added
# to the Indexer payload in LabelitScreen.py.
# 
# 
# 

import os
import sys
import copy

if not os.environ.has_key('XIA2CORE_ROOT'):
    raise RuntimeError, 'XIA2CORE_ROOT not defined'
if not os.environ.has_key('DPA_ROOT'):
    raise RuntimeError, 'DPA_ROOT not defined'

if not os.path.join(os.environ['XIA2CORE_ROOT'],
                    'Python') in sys.path:
    sys.path.append(os.path.join(os.environ['XIA2CORE_ROOT'],
                                 'Python'))
    
if not os.environ['DPA_ROOT'] in sys.path:
    sys.path.append(os.environ['DPA_ROOT'])

from Driver.DriverFactory import DriverFactory

def LabelitMosflmScript(DriverType = None):
    '''Factory for LabelitMosflmScript wrapper classes, with the specified
    Driver type.'''

    DriverInstance = DriverFactory.Driver(DriverType)

    class LabelitMosflmScriptWrapper(DriverInstance.__class__):
        '''A wrapper for the program labelit.mosflm_script - which will
        calculate the matrix for mosflm integration.'''

        def __init__(self):

            DriverInstance.__class__.__init__(self)
            self.set_executable('labelit.mosflm_script')

            self._solution = None

            return

        def set_solution(self, solution):
            self._solution = solution

            return

        def calculate(self):
            '''Compute matrix for solution #.'''

            if self._solution is None:
                raise RuntimeError, 'solution not selected'

            task = 'Compute matrix for solution %02d' % self._solution

            self.add_command_line('%d' % self._solution)

            self.start()
            self.close_wait()

            output = open(os.path.join(self.get_working_directory(),
                                       'integration%02d.csh' % self._solution)
                         ).readlines()
            matrix = output[2:11]

            return matrix

    return LabelitMosflmScriptWrapper()

if __name__ == '__main__':

    lms = LabelitMosflmScript()
    lms.set_solution(9)
    for m in lms.calculate():
        print m[:-1]

