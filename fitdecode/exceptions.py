# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.


class FitError(Exception):
    pass


class FitHeaderError(FitError):
    pass


class FitCrcError(FitError):
    pass


class FitEOFError(FitError):
    def __init__(self, expected, got, offset, message=''):
        self.expected = expected  # count of bytes
        self.got = got
        self.offset = offset

        desc = f'expected {self.expected} bytes, got {self.got} @ {self.offset}'
        if not message:
            message = desc
        else:
            message += ' (' + desc + ')'

        super().__init__(message)


class FitParseError(FitError):
    def __init__(self, offset, message=''):
        desc = 'FIT parsing error @ ' + str(offset)
        if message:
            desc += ': ' + message
        super().__init__(desc)
