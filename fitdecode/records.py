# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.


__all__ = [
    'FitChunk', 'FitHeader', 'FitCrc', 'FitDefinitionMessage', 'FitDataMessage']


class FitChunk:
    __slots__ = ('index', 'offset', 'bytes')

    def __init__(self, index, offset, bytes):
        self.index = index
        self.offset = offset
        self.bytes = bytes


class FitHeader:
    __slots__ = (
        'header_size', 'proto_ver', 'profile_ver', 'body_size',
        'crc', 'chunk')

    def __init__(self, header_size, proto_ver, profile_ver, body_size,
                 crc, chunk):
        self.header_size = header_size
        self.proto_ver = proto_ver
        self.profile_ver = profile_ver
        self.body_size = body_size
        self.crc = crc  #: may be null
        self.chunk = chunk


class FitCrc:
    __slots__ = ('crc', 'chunk')

    def __init__(self, crc, chunk):
        self.crc = crc
        self.chunk = chunk


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
        self.chunk = chunk

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
        self.chunk = chunk

    def __iter__(self):
        # sort by whether this is a known field, then its name
        # return iter(sorted(
        #     self.fields, key=lambda fd: (int(fd.field is None), fd.name)))

        return iter(self.fields)

    @property
    def name(self):
        return self.def_mesg.name

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
