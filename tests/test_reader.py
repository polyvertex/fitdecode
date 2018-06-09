#!/usr/bin/env python
#
# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

import glob
import hashlib
import os.path
import unittest

import fitdecode

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
HASH_METHOD = 'sha1'


# def _valid_file(name):
#     return os.path.join(TEST_FILES_DIR, name)


def _invalid_file(name):
    return os.path.join(TEST_FILES_DIR, 'invalid', name)


class RawChunkMatching(unittest.TestCase):

    def test_raw_chunk_parsing(self):
        """
        Test that FitReader parses correctly all our "valid" test files by
        building an in-memory clone of each source file, chunk by chunk, and
        then match file's and bytes object's checksums
        """
        src_pattern = os.path.join(TEST_FILES_DIR, '*.fit')
        for src_file in glob.iglob(src_pattern):
            raw_content = b''

            # read src_file chunk by chunk
            try:
                with fitdecode.FitReader(
                        src_file, check_crc=True, keep_raw_chunks=True) as fit:
                    for record in fit:
                        raw_content += record.chunk.bytes
            except Exception:
                print('ERROR while parsing:', src_file)
                raise

            # checksum of src_file
            h1 = hashlib.new(HASH_METHOD)
            with open(src_file, mode='rb') as fin:
                for buff in iter(lambda: fin.read(64 * 1024), b''):
                    h1.update(buff)

            # checksum of raw_content
            h2 = hashlib.new(HASH_METHOD)
            h2.update(raw_content)

            # compare checksums
            self.assertEqual(h1.digest(), h2.digest())

    def test_fitparse_elemnt_bolt_developer_data_id_without_application_id(self):
        """
        Test that a file without application id set inside developer_data_id is
        parsed (as seen on ELEMNT BOLT with firmware version WB09-1507)
        """
        tuple(fitdecode.FitReader(
            _invalid_file('elemnt-bolt-no-application-id-inside-developer-data-id.fit'),
            check_crc=True,
            keep_raw_chunks=True))


if __name__ == '__main__':
    unittest.main()
