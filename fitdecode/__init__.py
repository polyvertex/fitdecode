# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

from sys import version_info
if version_info < (3, 6):
    raise ImportError('fitdecode requires Python 3.6+')
del version_info

from .__version__ import (
    __version__, version_info,
    __title__, __fancy_title__, __description__, __url__,
    __license__, __author__, __copyright__)

from .exceptions import *
from .records import *
from .reader import *
from .processors import *

from . import processors
from . import profile
from . import reader
from . import types
from . import utils
