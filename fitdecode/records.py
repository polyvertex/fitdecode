# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.


__all__ = [
    'FitChunk', 'FitHeader', 'FitCRC', 'FitDefinitionMessage', 'FitDataMessage',
    'FIT_FRAME_HEADER', 'FIT_FRAME_CRC',
    'FIT_FRAME_DEFMESG', 'FIT_FRAME_DATAMESG']


_UNSET = object()

FIT_FRAME_HEADER = 1
FIT_FRAME_CRC = 2
FIT_FRAME_DEFMESG = 3
FIT_FRAME_DATAMESG = 4


class FitChunk:
    __slots__ = ('index', 'offset', 'bytes')

    def __init__(self, index, offset, bytes):
        self.index = index    #: zero-based index of this frame in the file
        self.offset = offset  #: the offset at which this frame starts in the file
        self.bytes = bytes    #: the frame itself as a `bytes` object


class FitHeader:
    frame_type = FIT_FRAME_HEADER

    __slots__ = (
        'header_size', 'proto_ver', 'profile_ver', 'body_size',
        'crc', 'crc_matched', 'chunk')

    def __init__(self, header_size, proto_ver, profile_ver, body_size,
                 crc, crc_matched, chunk):
        self.header_size = header_size
        self.proto_ver = proto_ver
        self.profile_ver = profile_ver
        self.body_size = body_size
        self.crc = crc  #: may be null
        self.crc_matched = crc_matched
        self.chunk = chunk  #: `FitChunk` or `None` (depends on ``keep_raw_chunks`` option)


class FitCRC:
    frame_type = FIT_FRAME_CRC

    __slots__ = ('crc', 'matched', 'chunk')

    def __init__(self, crc, matched, chunk):
        self.crc = crc
        self.matched = matched
        self.chunk = chunk  #: `FitChunk` or `None` (depends on ``keep_raw_chunks`` option)


class FitDefinitionMessage:
    frame_type = FIT_FRAME_DEFMESG

    __slots__ = (
        # record header
        'is_developer_data',
        'local_mesg_num',
        'time_offset',

        # payload
        'mesg_type',
        'global_mesg_num',
        'endian',
        'field_defs',
        'dev_field_defs',

        'chunk')

    def __init__(self, is_developer_data, local_mesg_num, time_offset,
                 mesg_type, global_mesg_num, endian, field_defs, dev_field_defs,
                 chunk):
        self.is_developer_data = is_developer_data
        self.local_mesg_num = local_mesg_num
        self.time_offset = time_offset
        self.mesg_type = mesg_type
        self.global_mesg_num = global_mesg_num
        self.endian = endian
        self.field_defs = field_defs  #: list of `FieldDefinition`
        self.dev_field_defs = dev_field_defs  #: list of `DevFieldDefinition`
        self.chunk = chunk  #: `FitChunk` or `None` (depends on ``keep_raw_chunks`` option)

    @property
    def name(self):
        if self.mesg_type:
            return self.mesg_type.name
        else:
            return 'unknown_' + str(self.global_mesg_num)


class FitDataMessage:
    frame_type = FIT_FRAME_DATAMESG

    __slots__ = (
        # record header
        'is_developer_data',
        'local_mesg_num',
        'time_offset',

        'def_mesg',
        'fields',
        'chunk')

    def __init__(self, is_developer_data, local_mesg_num, time_offset, def_mesg,
                 fields, chunk):
        self.is_developer_data = is_developer_data
        self.local_mesg_num = local_mesg_num
        self.time_offset = time_offset
        self.def_mesg = def_mesg  #: `FitDefinitionMessage`
        self.fields = fields  #: list of `FieldData`
        self.chunk = chunk  #: `FitChunk` or `None` (depends on ``keep_raw_chunks`` option)

    def __iter__(self):
        # sort by whether this is a known field, then its name
        # return iter(sorted(
        #     self.fields, key=lambda fd: (int(fd.field is None), fd.name)))

        return iter(self.fields)

    @property
    def name(self):
        return self.def_mesg.name

    @property
    def global_mesg_num(self):
        return self.def_mesg.global_mesg_num

    @property
    def mesg_type(self):
        return self.def_mesg.mesg_type

    def get_field(self, field_name_or_num):
        for field in self.fields:
            if field.is_named(field_name_or_num):
                return field

        raise KeyError(
            f'field "{field_name_or_num}" not found in message "{self.name}"')

    def get_value(self, field_name_or_num, *,
                  fallback=_UNSET, raw_value=False,
                  fit_type=None, py_type=_UNSET):
        """
        Get the value (or raw_value) of a field specified by its name or its
        definition number (*field_name_or_num*), with optional type checking.

        *fallback* can be specified to avoid `KeyError` being raised in case no
        field matched *field_name_or_num*.

        *fit_type* can be a `str` to indicate a given FIT type is expected (as
        defined in FIT profile; e.g. ``date_time``, ``manufacturer``, ...), in
        which case `TypeError` may be raised in case of a type mismatch.

        *py_type* can be a Python type or a `tuple` of types to expect (as
        passed to `isinstance`), in which case `TypeError` may be raised in case
        of a type mismatch.

        *raw_value* can be set to a true value so that the returned value is
        field's ``raw_value`` property instead of ``value``. This does not
        impact the way *fit_type* and *py_type* are interpreted.
        """
        assert fit_type in (_UNSET, None) or isinstance(fit_type, str)

        field_data = None

        for field in self.fields:
            if field.is_named(field_name_or_num):
                field_data = field
                break

        if not field_data:
            if fallback is _UNSET:
                raise KeyError(
                    f'field "{field_name_or_num}" not found in message ' +
                    f'"{self.name}"')
            return fallback

        # check FIT type if needed
        if fit_type and field_data.type.name != fit_type:
            raise TypeError(
                'unexpected type for FIT field ' +
                f'"{self.name}.{field_name_or_num}" ' +
                f'(got {field_data.type.name} instead of {fit_type})')

        # pick the right property
        value = field_data.value if not raw_value else field_data.raw_value

        # check value's type if needed
        if py_type is not _UNSET and not isinstance(value, py_type):
            if isinstance(py_type, (tuple, list)):
                py_type_str = ' or '.join([str(type(t)) for t in py_type])
            else:
                py_type_str = str(type(py_type))

            raise TypeError(
                'unexpected type for FIT value ' +
                f'"{self.name}.{field_name_or_num}" ' +
                f'(got {type(value)} instead of {py_type_str})')

        return value
