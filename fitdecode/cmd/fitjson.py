#!/usr/bin/env python3
# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import argparse
from collections import OrderedDict
import datetime
import json
import types
import sys
import traceback

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
                ('crc_matched', obj.crc_matched),
                ('chunk', obj.chunk)))

        if isinstance(obj, fitdecode.FitCRC):
            return OrderedDict((
                ('frame_type', 'crc'),
                ('crc', f'{obj.crc:#06x}'),
                ('matched', obj.matched),
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
        '-o', '--output', type=argparse.FileType(mode='wt', encoding='utf-8'),
        default='-',
        help='File to output data into (defaults to stdout)')

    parser.add_argument(
        'infile', metavar='FITFILE', type=argparse.FileType(mode='rb'),
        help='Input .FIT file (use - for stdin)')

    parser.add_argument(
        '--nocrc', action='store_const',
        default=fitdecode.CrcCheck.ENABLED,
        const=fitdecode.CrcCheck.DISABLED,
        help="Some devices seem to write invalid CRC's, ignore these.")

    parser.add_argument(
        '--nodef', action='store_const', const=True,
        help="Do not output FIT so-called local message definitions.")

    parser.add_argument(
        '-f', '--filter', action='append',
        help=(
            'Message name(s) (or global numbers) to filter-in ' +
            '(other messages are then ignored).'))

    options = parser.parse_args(args)

    return options


def main(args=None):
    options = parse_args(args)

    frames = []

    try:
        with fitdecode.FitReader(
                options.infile,
                processor=fitdecode.StandardUnitsDataProcessor(),
                check_crc=options.nocrc,
                keep_raw_chunks=True) as fit:
            for frame in fit:
                if options.nodef and isinstance(
                        frame, fitdecode.FitDefinitionMessage):
                    continue

                if (options.filter and
                        isinstance(frame, (
                            fitdecode.FitDefinitionMessage,
                            fitdecode.FitDataMessage)) and
                        (frame.name not in options.filter) and
                        (frame.global_mesg_num not in options.filter)):
                    continue

                frames.append(frame)
    except Exception:
        print(
            'WARNING: the following error occurred while parsing FIT file. '
            'Output file might be incomplete or corrupted.',
            file=sys.stderr)
        print('', file=sys.stderr)
        traceback.print_exc()

    json.dump(frames, fp=options.output, cls=RecordJSONEncoder)

    return 0


if __name__ == '__main__':
    sys.exit(main())
