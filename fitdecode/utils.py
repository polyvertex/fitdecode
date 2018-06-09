# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

import re
import time

__all__ = []


METHOD_NAME_SCRUBBER = re.compile(r'\W|^(?=\d)')
UNIT_NAME_TO_FUNC_REPLACEMENTS = (
    ('/', ' per '),
    ('%', 'percent'),
    ('*', ' times '))

CRC_START = 0
CRC_TABLE = (
    0x0000, 0xcc01, 0xd801, 0x1400, 0xf001, 0x3c00, 0x2800, 0xe401,
    0xa001, 0x6c00, 0x7800, 0xb401, 0x5000, 0x9c01, 0x8801, 0x4400)


def scrub_method_name(method_name, convert_units=False):
    if convert_units:
        for replace_from, replace_to in UNIT_NAME_TO_FUNC_REPLACEMENTS:
            method_name = method_name.replace(replace_from, str(replace_to))

    return METHOD_NAME_SCRUBBER.sub('_', method_name)


def compute_crc(byteslike, *, crc=CRC_START, start=0, end=None):
    if not end:
        end = len(byteslike)

    if start >= end:
        assert 0
        return crc

    # According to some performance tests, A is always (at least slightly)
    # faster than B, either with a high number of calls to this fonction, and/or
    # with a high number of "for" iterations (CPython 3.6.5 x64 on Windows).
    #
    # A. for byte in memoryview(byteslike)[start:end]:
    #        # ...
    #
    # B. for idx in range(start, end):
    #        byte = byteslike[idx]
    #        # ...

    for byte in memoryview(byteslike)[start:end]:
        tmp = CRC_TABLE[crc & 0xf]
        crc = (crc >> 4) & 0x0fff
        crc = crc ^ tmp ^ CRC_TABLE[byte & 0xf]

        tmp = CRC_TABLE[crc & 0xf]
        crc = (crc >> 4) & 0x0fff
        crc = crc ^ tmp ^ CRC_TABLE[(byte >> 4) & 0xf]

    return crc


def blocking_read(istream, size=-1, nonblocking_reads_delay=0.06):
    """
    Read from *istream* and do not return until *size* `bytes` have been read
    unless EOF has been reached.

    Return all the data read so far. The length of the returned data may still
    be less than *size* in case EOF has been reached.

    *nonblocking_reads_delay* specifies the number of seconds (float) to wait
    before trying to read from *istream* again in case `BlockingIOError` has
    been raised during previous call.
    """
    if not size:
        return None

    data = b''
    while True:
        try:
            chunk = istream.read(-1 if size < 0 else size - len(data))

            if not data:
                data = chunk
            else:
                data += chunk

            if not chunk or (size > 0 and len(data) >= size):
                return data
        except BlockingIOError:
            time.sleep(nonblocking_reads_delay)
