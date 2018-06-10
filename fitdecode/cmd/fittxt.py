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
import decimal
import os.path

import fitdecode

echo = None


def txt_encode(obj):
    """
    Convert a given *obj* to either a *str* or *PrintableObject* (most suitable)
    """

    if isinstance(obj, PrintableObject):
        return obj

    if isinstance(obj, str):
        return '[' + obj + ']'

    if obj is None:
        return '<none>'

    if isinstance(obj, bool):
        return 'yes' if obj else 'no'

    if isinstance(obj, (int, float, decimal.Decimal)):
        return str(obj)

    if isinstance(obj, datetime.time):
        return obj.isoformat()

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    if isinstance(obj, fitdecode.FitChunk):
        return PrintableObject(
            index=obj.index,
            offset=obj.offset,
            size=len(obj.bytes))

    if isinstance(obj, fitdecode.types.FieldDefinition):
        return PrintableObject(
            name=obj.name,
            def_num=obj.def_num,
            type_name=obj.type.name,
            base_type_name=obj.base_type.name,
            size=obj.size)

    if isinstance(obj, fitdecode.types.DevFieldDefinition):
        return PrintableObject(
            name=obj.name,
            dev_data_index=obj.dev_data_index,
            def_num=obj.def_num,
            type_name=obj.type.name,
            size=obj.size)

    if isinstance(obj, fitdecode.types.FieldData):
        return PrintableObject(
            name=obj.name,
            value=obj.value,
            units=obj.units if obj.units else '',
            def_num=obj.def_num,
            raw_value=obj.raw_value)

    if isinstance(obj, fitdecode.FitHeader):
        crc = obj.crc if obj.crc else 0
        return PrintableObject(
            _label='fit_header',
            header_size=obj.header_size,
            proto_ver='(' + ', '.join([str(v) for v in obj.proto_ver]) + ')',
            profile_ver='(' + ', '.join([str(v) for v in obj.profile_ver]) + ')',
            body_size=obj.body_size,
            crc=f'{crc:#06x}',
            crc_matched=obj.crc_matched,
            chunk=obj.chunk)

    if isinstance(obj, fitdecode.FitCRC):
        return PrintableObject(
            _label='fit_crc',
            crc=f'{obj.crc:#06x}',
            matched=obj.matched,
            chunk=obj.chunk)

    if isinstance(obj, fitdecode.FitDefinitionMessage):
        return PrintableObject(
            _label='fit_definition [' + obj.name + ']',
            header=PrintableObject(
                local_mesg_num=obj.local_mesg_num,
                time_offset=obj.time_offset,
                is_developer_data=obj.is_developer_data),
            global_mesg_num=obj.global_mesg_num,
            endian=obj.endian,
            field_defs=obj.field_defs,
            dev_field_defs=obj.dev_field_defs,
            chunk=obj.chunk)

    if isinstance(obj, fitdecode.FitDataMessage):
        return PrintableObject(
            _label='fit_data [' + obj.name + ']',
            header=PrintableObject(
                local_mesg_num=obj.local_mesg_num,
                time_offset=obj.time_offset,
                is_developer_data=obj.is_developer_data),
            fields=obj.fields,
            chunk=obj.chunk)

    if __debug__:
        print(type(obj))
        assert 0

    return repr(obj)


class PrintableObject:
    __slots__ = (
        '_label', '_dict', '_max_key_length',
        '_pad', '_key_prefix', '_key_suffix')

    def __init__(self, *, _label=None, _pad=' ', _key_prefix='',
                 _key_suffix='  ', **props):
        self._label = _label
        self._dict = OrderedDict()
        self._max_key_length = 0
        self._pad = _pad
        self._key_prefix = _key_prefix
        self._key_suffix = _key_suffix

        for key, value in props.items():
            # to avoid potential collision with PrintableObject members
            assert key[0] != '_'

            self._dict[key] = value
            if len(key) > self._max_key_length:
                self._max_key_length = len(key)

    def __iter__(self):
        for key, value in self._dict.items():
            name = self._key_prefix
            name += key.ljust(self._max_key_length, self._pad)
            name += self._key_suffix

            yield name, value

    def __getattr__(self, name):
        try:
            return self._dict[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        if name[0] == '_':
            super().__setattr__(name, value)
        elif name not in self._dict:
            raise AttributeError
        else:
            self._dict[name] = value


def global_stats(frames, options):
    stats = PrintableObject(
        _label='TXT',
        name=os.path.basename(options.infile.name),
        frames=len(frames),
        size=0,
        missing_headers=0,
        fit_files=[])

    stats_got_header = False
    for frame in frames:
        stats.size += len(frame.chunk.bytes)

        if isinstance(frame, fitdecode.FitHeader):
            stats_got_header = True
            stats.fit_files.append(PrintableObject(
                data_messages=0,
                definition_messages=0,
                has_footer=False,
                header_crc_matched=frame.crc_matched,
                footer_crc_matched=False))
            continue

        if not stats_got_header:
            stats.missing_headers += 1
            continue

        curr_file = stats.fit_files[-1]

        if isinstance(frame, fitdecode.FitCRC):
            stats_got_header = False
            curr_file.has_footer = True
            curr_file.footer_crc_matched = frame.matched

        elif isinstance(frame, fitdecode.FitDefinitionMessage):
            curr_file.definition_messages += 1

        elif isinstance(frame, fitdecode.FitDataMessage):
            curr_file.data_messages += 1

    return stats


def txt_print(obj, *, indent=' ' * 4, level=0):

    def _recurse(subobj, sublevel=level):
        txt_print(subobj, indent=indent, level=sublevel)

    def _p(*values, end='\n'):
        echo(indent * level, *values, sep='', end=end)

    if isinstance(obj, str):
        _p(obj)

    elif isinstance(obj, (tuple, list)):
        first = True
        for value in obj:
            if first:
                first = False
            else:
                _p('-')
            _recurse(value)

    elif isinstance(obj, PrintableObject):
        if obj._label:
            _p(obj._label)
            obj._label = None
            _recurse(obj, sublevel=level + 1)
        else:
            for key, value in obj:
                if isinstance(value, str):
                    _p(key, value)
                elif isinstance(value, (tuple, list)):
                    _p(f'{key.rstrip()} ({len(value)})')
                    _recurse(value, sublevel=level + 1)
                else:
                    value = txt_encode(value)
                    if isinstance(value, str):
                        _p(key, value)
                    else:
                        _p(key.rstrip())
                        _recurse(value, sublevel=level + 1)

    else:
        _recurse(txt_encode(obj))


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Dump a FIT file to TXT format',
        epilog='fitdecode version ' + fitdecode.__version__)

    parser.add_argument(
        '-o', '--output', type=argparse.FileType(mode='wt'), default='-',
        help='File to output data into (defaults to stdout)')

    parser.add_argument(
        'infile', metavar='FITFILE', type=argparse.FileType(mode='rb'),
        help='Input .FIT file (use - for stdin)')

    parser.add_argument(
        '--ignore-crc', action='store_const', const=True,
        help="Some devices seem to write invalid CRC's, ignore these.")

    options = parser.parse_args(args)

    return options


def main(args=None):
    options = parse_args(args)

    def _echo(*objects, sep=' ', end='\n', file=options.output, flush=False):
        print(*objects, sep=sep, end=end, file=file, flush=flush)

    def _echo_separator():
        _echo('')
        _echo('*' * 80)
        _echo('')
        _echo('')

    global echo
    echo = _echo

    # fully parse input file
    frames = tuple(fitdecode.FitReader(
        options.infile,
        processor=fitdecode.StandardUnitsDataProcessor(),
        check_crc=not(options.ignore_crc),
        keep_raw_chunks=True))

    # print some statistics before starting
    txt_print(global_stats(frames, options))
    echo('')

    # pretty-print the file
    had_frames = False
    for frame in frames:
        if had_frames and isinstance(frame, fitdecode.FitHeader):
            _echo_separator()
        had_frames = True
        txt_print(frame)
        echo('')


if __name__ == '__main__':
    main()
