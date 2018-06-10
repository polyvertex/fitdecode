#!/usr/bin/env python
#
# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

import argparse
from collections import OrderedDict
import datetime
import json
import types

import fitdecode


class RecordJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, types.GeneratorType):
            return list(obj)

        if isinstance(obj, datetime.time):
            return obj.isoformat()

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        if isinstance(obj, fitdecode.FitChunk):
            return OrderedDict((
                ('index', obj.index),
                ('offset', obj.offset),
                ('size', len(obj.bytes))))

        if isinstance(obj, fitdecode.types.FieldDefinition):
            return OrderedDict((
                ('name', obj.name),
                ('def_num', obj.def_num),
                ('type_name', obj.type.name),
                ('base_type_name', obj.base_type.name),
                ('size', obj.size)))

        if isinstance(obj, fitdecode.types.DevFieldDefinition):
            return OrderedDict((
                ('name', obj.name),
                ('dev_data_index', obj.dev_data_index),
                ('def_num', obj.def_num),
                ('type_name', obj.type.name),
                ('size', obj.size)))

        if isinstance(obj, fitdecode.types.FieldData):
            return OrderedDict((
                ('name', obj.name),
                ('value', obj.value),
                ('units', obj.units if obj.units else ''),
                ('def_num', obj.def_num),
                ('raw_value', obj.raw_value)))

        if isinstance(obj, fitdecode.FitHeader):
            crc = obj.crc if obj.crc else 0
            return OrderedDict((
                ('frame_type', 'header'),
                ('header_size', obj.header_size),
                ('proto_ver', obj.proto_ver),
                ('profile_ver', obj.profile_ver),
                ('body_size', obj.body_size),
                ('crc', f'{crc:#06x}'),
                ('chunk', obj.chunk)))

        if isinstance(obj, fitdecode.FitCrc):
            return OrderedDict((
                ('frame_type', 'crc'),
                ('crc', f'{obj.crc:#06x}'),
                ('chunk', obj.chunk)))

        if isinstance(obj, fitdecode.FitDefinitionMessage):
            return OrderedDict((
                ('frame_type', 'definition_message'),
                ('name', obj.name),
                ('header', OrderedDict((
                    ('local_mesg_num', obj.local_mesg_num),
                    ('time_offset', obj.time_offset),
                    ('is_developer_data', obj.is_developer_data)))),
                ('global_mesg_num', obj.global_mesg_num),
                ('endian', obj.endian),
                ('field_defs', obj.field_defs),
                ('dev_field_defs', obj.dev_field_defs),
                ('chunk', obj.chunk)))

        if isinstance(obj, fitdecode.FitDataMessage):
            return OrderedDict((
                ('frame_type', 'data_message'),
                ('name', obj.name),
                ('header', OrderedDict((
                    ('local_mesg_num', obj.local_mesg_num),
                    ('time_offset', obj.time_offset),
                    ('is_developer_data', obj.is_developer_data)))),
                ('fields', obj.fields),
                ('chunk', obj.chunk)))

        # fall back to original to raise a TypeError
        return super().default(obj)


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Dump a FIT file to JSON format',
        epilog='fitdecode version ' + fitdecode.__version__)

    parser.add_argument(
        '-v', '--verbose', action='count', default=0)

    parser.add_argument(
        '-o', '--output', type=argparse.FileType(mode='w'), default="-",
        help='File to output data into (defaults to stdout)')

    parser.add_argument(
        'infile', metavar='FITFILE', type=argparse.FileType(mode='rb'),
        help='Input .FIT file (use - for stdin)')

    parser.add_argument(
        '--ignore-crc', action='store_const', const=True,
        help="Some devices seem to write invalid CRC's, ignore these.")

    options = parser.parse_args(args)

    options.verbose = options.verbose >= 1

    return options


def main(args=None):
    options = parse_args(args)

    frames = tuple(fitdecode.FitReader(
            options.infile,
            processor=fitdecode.StandardUnitsDataProcessor(),
            check_crc=not(options.ignore_crc),
            keep_raw_chunks=True))

    json.dump(frames, fp=options.output, cls=RecordJSONEncoder)


if __name__ == '__main__':
    main()
