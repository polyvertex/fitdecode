#!/usr/bin/env python
#
# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

import os.path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fitdecode.cmd import fittxt

if __name__ == '__main__':
    fittxt.main()
