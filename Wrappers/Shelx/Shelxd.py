#!/usr/bin/env python
# FileName.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
#
# 16th November 2006
# 

import sys
import os

if not os.path.join(os.environ['XIA2CORE_ROOT'], 'Python') in sys.path:
    sys.path.append(os.path.join(os.environ['XIA2CORE_ROOT'], 'Python'))

if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.environ['XIA2_ROOT'])


