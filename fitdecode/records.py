# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.


__all__ = [
    'FitChunk', 'FitHeader', 'FitCRC', 'FitDefinitionMessage', 'FitDataMessage']


class FitChunk:
    __slots__ = ('index', 'offset', 'bytes')

    def __init__(self, index, offset, bytes):
        self.index = index    #: zero-based index of this frame in the file
        self.offset = offset  #: the offset at which this frame starts in the file
        self.bytes = bytes    #: the frame itself as a `bytes` object


class FitHeader:
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
    __slots__ = ('crc', 'matched', 'chunk')

    def __init__(self, crc, matched, chunk):
        self.crc = crc
        self.matched = matched
        self.chunk = chunk  #: `FitChunk` or `None` (depends on ``keep_raw_chunks`` option)


class FitDefinitionMessage:
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
        self.field_defs = field_defs
        self.dev_field_defs = dev_field_defs
        self.chunk = chunk  #: `FitChunk` or `None` (depends on ``keep_raw_chunks`` option)

    @property
    def name(self):
        if self.mesg_type:
            return self.mesg_type.name
        else:
            return 'unknown_' + str(self.global_mesg_num)


class FitDataMessage:
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
        self.fields = fields
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

    def get_field(self, field_name):
        for field in self.fields:
            if field.is_named(field_name):
                return field

        # should we just return None instead?
        raise KeyError(
            f'field named "{field_name}" not found in message "{self.name}"')
