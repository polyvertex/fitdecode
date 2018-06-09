#!/usr/bin/env python
#
# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

import csv
import datetime
import glob
import hashlib
import os.path
import struct
import unittest

import fitdecode

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
HASH_METHOD = 'sha1'


def _test_file(name):
    return os.path.join(TEST_FILES_DIR, name)


def _invalid_test_file(name):
    return os.path.join(TEST_FILES_DIR, 'invalid', name)


def _secs_to_dt(secs):
    return datetime.datetime.fromtimestamp(
        secs + fitdecode.FIT_UTC_REFERENCE,
        datetime.timezone.utc)


def _generate_messages(mesg_num, local_mesg_num, field_defs,
                       endian='<', data=None):
    mesgs = []
    base_type_list = []

    # definition message, local message num
    s = struct.pack('<B', 0x40 | local_mesg_num)

    # reserved byte and endian
    s += struct.pack('<xB', int(endian == '>'))

    # global message num, num fields
    s += struct.pack('%sHB' % endian, mesg_num, len(field_defs))

    for def_num, base_type in field_defs:
        base_type = [
            bt for bt in fitdecode.types.BASE_TYPES.values()
            if bt.name == base_type][0]
        base_type_list.append(base_type)
        s += struct.pack('<3B', def_num, base_type.size, base_type.identifier)

    mesgs.append(s)

    if data:
        for mesg_data in data:
            s = struct.pack('B', local_mesg_num)
            for value, base_type in zip(mesg_data, base_type_list):
                s += struct.pack("%s%s" % (endian, base_type.fmt), value)
            mesgs.append(s)

    return b''.join(mesgs)


def _generate_fitfile(data=None, endian='<'):
    fit_data = (_generate_messages(
        # local mesg 0, global mesg 0 (file_id)
        mesg_num=0, local_mesg_num=0, endian=endian, field_defs=[
            # serial number, time_created, manufacturer
            (3, 'uint32z'), (4, 'uint32'), (1, 'uint16'),
            # product/garmin_product, number, type
            (2, 'uint16'), (5, 'uint16'), (0, 'enum')],
        # random serial number, random time, garmin, edge500, null, activity
        data=[[558069241, 723842606, 1, 1036, (2 ** 16) - 1, 4]]))

    if data:
        fit_data += data

    # Prototcol version 1.0, profile version 1.52
    header = struct.pack('<2BHI4s', 14, 16, 152, len(fit_data), b'.FIT')

    file_data = \
        header + \
        struct.pack('<H', fitdecode.utils.compute_crc(header)) + \
        fit_data

    return \
        file_data + \
        struct.pack('<H', fitdecode.utils.compute_crc(file_data))


class FitReaderTestCase(unittest.TestCase):

    @unittest.skip('TEMPORARY SKIPPED TEST -- MUST BE REMOVED BEFORE COMMIT -- TODO XXX FIXME')
    def test_raw_chunk_parsing(self):
        """
        Test that FitReader parses correctly all our "valid" test files by
        building an in-memory clone of each source file, chunk by chunk, and
        then match file's and bytes object's checksums

        Files with developer types (at least)::

            developer-types-sample.fit
            20170518-191602-1740899583.fit
            DeveloperData.fit

        Chained files (at least)::

            activity-settings.fit
        """
        for src_file in glob.iglob(os.path.join(TEST_FILES_DIR, '*.fit')):
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

    def test_fitparse_invalid_crc(self):
        try:
            tuple(fitdecode.FitReader(
                _invalid_test_file('activity-filecrc.fit'),
                check_crc=True,
                keep_raw_chunks=True))
            self.fail('did not detect an invalid CRC')
        except fitdecode.FitCRCError:
            pass

    def test_fitparse_unexpected_eof(self):
        try:
            tuple(fitdecode.FitReader(
                _invalid_test_file('activity-unexpected-eof.fit'),
                check_crc=True,
                keep_raw_chunks=True))
            self.fail('did not detect an unexpected EOF')
        except fitdecode.FitEOFError:
            pass

    def test_fitparse_elemnt_bolt_developer_data_id_without_application_id(self):
        """
        Test that a file without application id set inside developer_data_id is
        parsed (as seen on ELEMNT BOLT with firmware version WB09-1507)
        """
        tuple(fitdecode.FitReader(
            _invalid_test_file('elemnt-bolt-no-application-id-inside-developer-data-id.fit'),
            check_crc=True,
            keep_raw_chunks=True))

    def test_fitparse_basic_file_with_one_record(self, endian='<'):
        fit = tuple(fitdecode.FitReader(
            _generate_fitfile(endian=endian),
            check_crc=True,
            keep_raw_chunks=False))

        file_header = fit[0]

        file_id = None
        for mesg in fit:
            if isinstance(mesg, fitdecode.FitDataMessage) and mesg.name == 'file_id':
                file_id = mesg
                break
        self.assertTrue(file_id, 'file_id not found')

        self.assertEqual(file_header.profile_ver, (1, 52))
        self.assertEqual(file_header.proto_ver, (1, 0))
        self.assertEqual(file_id.name, 'file_id')

        for field in ('type', 0):
            self.assertEqual(file_id.get_field(field).value, 'activity')
            self.assertEqual(file_id.get_field(field).raw_value, 4)

        for field in ('manufacturer', 1):
            self.assertEqual(file_id.get_field(field).value, 'garmin')
            self.assertEqual(file_id.get_field(field).raw_value, 1)

        for field in ('product', 'garmin_product', 2):
            self.assertEqual(file_id.get_field(field).value, 'edge500')
            self.assertEqual(file_id.get_field(field).raw_value, 1036)

        for field in ('serial_number', 3):
            self.assertEqual(file_id.get_field(field).value, 558069241)

        for field in ('time_created', 4):
            self.assertEqual(file_id.get_field(field).value, _secs_to_dt(723842606))
            self.assertEqual(file_id.get_field(field).raw_value, 723842606)

        for field in ('number', 5):
            self.assertEqual(file_id.get_field(field).value, None)

    def test_fitparse_basic_file_big_endian(self):
        self.test_fitparse_basic_file_with_one_record('>')

    def test_fitparse_component_field_accumulaters(self):
        csv_fp = open(
            _test_file('compressed-speed-distance-records.csv'),
            mode='rt')
        csv_file = csv.reader(csv_fp)
        next(csv_file)  # consume header

        # parse the whole content
        fit = tuple(fitdecode.FitReader(
            _test_file('compressed-speed-distance.fit'),
            check_crc=True,
            keep_raw_chunks=False))

        # build a generator of 'record' messages only
        records = (
            r for r in fit
            if isinstance(r, fitdecode.FitDataMessage)
            and r.name == 'record')

        # skip empty record for now (sets timestamp via header)
        empty_record = next(records)

        # file's timestamp record is < 0x10000000, so field returns seconds
        self.assertEqual(empty_record.get_field('timestamp').value, 17217864)

        # TODO: update using local_timestamp as offset, since we have this value
        # as 2012 date

        for count, (record, (timestamp, heartrate, speed, distance, cadence)) in enumerate(zip(records, csv_file)):
            # no fancy datetime stuff, since timestamp record is < 0x10000000
            fit_ts = record.get_field('timestamp').value

            self.assertIsInstance(fit_ts, int)
            self.assertLess(fit_ts, 0x10000000)
            self.assertEqual(fit_ts, int(timestamp))

            self.assertEqual(record.get_field('heart_rate').value, int(heartrate))
            self.assertEqual(record.get_field('cadence').value, int(cadence) if cadence != 'null' else None)
            self.assertAlmostEqual(record.get_field('speed').value, float(speed))
            self.assertAlmostEqual(record.get_field('distance').value, float(distance))

        self.assertEqual(count, 753)  # TODO: confirm size(records) = size(csv)
        csv_fp.close()


if __name__ == '__main__':
    unittest.main()
