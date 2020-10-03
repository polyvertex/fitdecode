# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import enum
import io
import os
import struct

from .exceptions import FitHeaderError, FitCRCError, FitEOFError, FitParseError
from . import records
from . import types
from . import utils
from . import processors
from . import profile

__all__ = ['CrcCheck', 'FitReader']

_UNSET = object()


class CrcCheck(enum.Enum):
    """
    Defines the values expected by the ``check_crc`` parameter of `FitReader`'s
    constructor.
    """

    #: CRC is not computed at all (fastest).
    #: :class:`fitdecode.FitCRC` frame will still be yielded if present in the
    #: source FIT stream, but with meaningless values. In which case data
    #: processor's `fitdecode.DataProcessorBase.on_crc` method will still be
    #: called as well.
    DISABLED = 0

    #: CRC is computed but `FitReader` will never try to match CRCs. So no
    #: :class:`fitdecode.FitCRCError` will ever be raised.
    READONLY = 1

    #: CRC is computed and matched by `FitReader`.
    #: :class:`fitdecode.FitCRCError` is raised upon incorrect CRC values.
    ENABLED = 2


class RecordHeader:
    __slots__ = (
        'is_definition', 'is_developer_data', 'local_mesg_num', 'time_offset')

    def __init__(self, is_definition, is_developer_data, local_mesg_num,
                 time_offset):
        self.is_definition = is_definition
        self.is_developer_data = is_developer_data
        self.local_mesg_num = local_mesg_num
        self.time_offset = time_offset


class FitReader:
    """
    Parse the content of a FIT stream or storage.

    Transparently supports "chained FIT Files" as per SDK's definition. A
    `FitHeader` object is yielded during iteration to mark the beginning of each
    new "FIT File".

    Usage::

        import fitdecode

        with fitdecode.FitReader('file.fit') as fit:
            for frame in fit:
                # The yielded frame object is of one of the following types:
                # * fitdecode.FitHeader
                # * fitdecode.FitDefinitionMessage
                # * fitdecode.FitDataMessage
                # * fitdecode.FitCRC

                if isinstance(frame, fitdecode.FitDataMessage):
                    # Here, frame is a FitDataMessage object.
                    # A FitDataMessage object contains decoded values that
                    # are directly usable in your script logic.
                    print(frame.name)

    Data processing:

    * You can specify your own data processor object using the *processor*
      argument.
    * The argument can be left untouched so that `DefaultDataProcessor` is used.
    * Otherwise, it can be set to `None` or any other false value to skip data
      processing entirely. This can speed up things a bit if your intent is only
      to manipulate the file at binary level (i.e. chunks), in which case
      *keep_raw_chunks* must be set to true.

    Raw chunks:

    * "raw chunk" or sometimes "frame", is the name given in fitdecode to the
      `bytes` block that represents one of the four FIT entities: `FitHeader`,
      `FitDefinitionMessage`, `FitDataMessage` and `FitCRC`.
    * While iterating a file with `FitReader`, you can for instance cut, stitch
      and/or reconstruct the file being read by using the
      `FitChunk` object attached to any of the four aforementioned entities, as
      long as the *keep_raw_chunks* option is true.

    Data bag:

    * A *data_bag* object can be passed to the constructor and then be retrieved
      via the `data_bag` property.
    * *data_bag* can be of any type (a `dict` by default) and will never be
      altered by this class.
    * A "data bag" is useful if you wish to store some context-sensitive data
      during the decoding of a file.
    * A typical use case is from a data processor that cannot hold its own
      context-sensitive data due to its instance being shared with other readers
      and/or by multiple threads (typically `DefaultDataProcessor`).

    """

    def __init__(self, fileish, *,
                 processor=_UNSET, check_crc=CrcCheck.ENABLED,
                 keep_raw_chunks=False, data_bag=_UNSET):
        # backward compatibility
        if check_crc is True:
            check_crc = CrcCheck.ENABLED
        elif check_crc is False:
            check_crc = CrcCheck.DISABLED
        assert isinstance(check_crc, CrcCheck)

        # modifiable options (public)
        self.check_crc = check_crc

        # state (public)
        #: the *data_bag* object that was passed to the constructor, or, by
        #: default, a `dict` object
        self.data_bag = {} if data_bag is _UNSET else data_bag

        # immutable options (private)
        if processor is _UNSET:
            self._processor = processors.DefaultDataProcessor()
        else:
            self._processor = processor
        self._keep_raw = keep_raw_chunks

        # state (private)
        self._fd = None        # the file object to read from
        self._read_offset = 0  # read cursor position in the file
        self._read_size = 0    # count bytes read from this file so far in total

        # per-chunk state (private)
        self._chunk_index = 0   # the index number of the current chunk that is currently being read
        self._chunk_offset = 0  # the offset of the current chunk (relative to `read_offset`)
        self._chunk_size = 0    # the size of the current chunk

        # per-FIT-file state (private)
        self._crc = utils.CRC_START  # current CRC value, updated upon every read, reset on each new "FIT file"
        self._header = None          # `FitHeader` of the **current** "FIT file"
        self._file_id = None         # last read file_id `FitDataMessage` object
        self._body_bytes_left = 0    # the number of bytes that are still to read before reaching the CRC footer of the current "FIT file"
        self._local_mesg_defs = {}   # registry of every `FitDefinitionMessage` in this file so far
        self._local_dev_types = {}   # registry of developer types
        self._compressed_ts_accumulator = 0  # state value for the so-called "Compressed Timestamp Header"
        self._accumulators = {}
        self._last_timestamp = 0
        self._hr_start_timestamp = 0  # special case for the ``hr`` message

        if hasattr(fileish, '__fspath__'):
            fileish = os.fspath(fileish)

        if hasattr(fileish, 'read'):
            self._fd = fileish
        elif isinstance(fileish, str):
            self._fd = open(fileish, mode='rb')
        else:
            self._fd = io.BytesIO(fileish)

        try:
            self._read_offset = self._fd.tell()
            self._chunk_offset = self._read_offset
        except (AttributeError, OSError):
            pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return self.close()

    def __iter__(self):
        yield from self._read_next()

    @property
    def processor(self):
        """Read-only access to the data processor object."""
        return self._processor

    @property
    def last_header(self):
        """The last read `FitHeader` object. May be `None`."""
        return self._header

    @property
    def last_timestamp(self):
        """
        The last ``timestamp`` value (`int`).

        Often useful in FIT files since some data fields rely on it like
        ``timestamp_16`` and ``timestamp_ms`` for instance.

        Hint: you usually want to use this property from your own processor
        class derived from on of the processors available from
        `fitdecode.processors`.
        """
        return self._last_timestamp

    @property
    def file_id(self):
        """The last read ``file_id`` `FitDataMessage` object. May be `None`."""
        return self._file_id

    @property
    def local_mesg_defs(self):
        """
        Read-only access to the `dict` of local message types of the current
        "FIT file".

        It is cleared by `close()` (or ``__exit__()``), and also each time a FIT
        file header is reached (i.e. at the beginning of a file, or after a
        `FitCRC`).
        """
        return self._local_mesg_defs

    @property
    def local_dev_types(self):
        """
        Read-only access to the `dict` of developer types of the current
        "FIT file".

        It is cleared by `close()` (or ``__exit__()``), and also each time a FIT
        file header is reached (i.e. at the beginning of a file, or after a
        `FitCRC`).
        """
        return self._local_dev_types

    def close(self):
        """
        Close the file handle (constructor's *fileish*) and clear the internal
        state.
        """
        if self._fd and hasattr(self._fd, 'close'):
            self._fd.close()

        self._fd = None
        self._read_offset = 0
        self._read_size = 0
        self._chunk_index = 0
        self._chunk_offset = 0
        self._chunk_size = 0
        self._crc = utils.CRC_START
        self._header = None
        self._file_id = None
        self._body_bytes_left = 0
        self._local_mesg_defs = {}
        self._local_dev_types = {}
        self._compressed_ts_accumulator = 0
        self._accumulators = {}
        self._last_timestamp = 0
        self._hr_start_timestamp = 0

    # ONLY PRIVATE METHODS BELOW ***********************************************

    def _read_next(self):

        def _update_state():
            if self._fd:
                self._chunk_index += 1
                self._chunk_offset += self._chunk_size
                self._chunk_size = 0

        while self._fd:
            assert self._chunk_size == 0

            if not self._header:
                assert self._body_bytes_left == 0

                self._on_new_file()
                self._read_header()
                if not self._header:
                    break

                yield self._header
                _update_state()

            elif self._body_bytes_left > 0:
                assert self._header

                record = self._read_record()
                if not record:
                    break

                assert self._chunk_size <= self._body_bytes_left
                self._body_bytes_left -= self._chunk_size

                yield record
                _update_state()

            else:
                assert self._header
                assert self._body_bytes_left == 0

                try:
                    crc_obj = self._read_crc()
                except FitEOFError:
                    # if self.check_crc != CrcCheck.ENABLED:
                    #     # There is no CRC footer in this file (or it is
                    #     # incomplete) but caller does not mind about CRC so
                    #     # we will just ignore this
                    #     break
                    raise

                yield crc_obj
                _update_state()

                # We've reached the end of this FIT file... To avoid incorrect
                # behavior due to malformed FIT stream (i.e. next FIT header
                # missing), reset the internal state now as well, instead of
                # resetting it only when a FIT header is read.
                self._on_new_file()

    def _on_new_file(self):
        # reset state
        self._crc = utils.CRC_START
        self._header = None
        self._body_bytes_left = 0
        self._local_mesg_defs = {}
        self._local_dev_types = {}
        self._compressed_ts_accumulator = 0
        self._accumulators = {}
        self._last_timestamp = 0
        self._hr_start_timestamp = 0

    def _read_header(self):
        try:
            chunk, header_size, proto_ver, profile_ver, body_size, \
                header_magic = self._read_struct('<2BHI4s')
        except FitEOFError as exc:
            if not exc.got:
                # regular EOF: storage is empty or previous "FIT file" ended
                # normally
                return
            raise FitHeaderError('file too small (' + str(exc) + ')')

        # check header size
        if header_size < len(chunk) or header_magic != b'.FIT':
            raise FitHeaderError('not a FIT file')

        # read the extended part of the header (i.e. byte 12-...)
        extra_header_size = header_size - len(chunk)
        read_crc = None
        crc_matched = None
        if extra_header_size:
            # at least 2 bytes expected for the CRC
            if extra_header_size < 2:
                raise FitHeaderError('unsupported FIT header')

            extra_chunk = self._read_bytes(extra_header_size)
            if len(extra_chunk) != extra_header_size:
                raise FitHeaderError('truncated FIT header')

            (read_crc, ) = struct.unpack('<H', extra_chunk)
            if not read_crc:  # can be null according to SDK
                read_crc = None
                crc_matched = None
            else:
                computed_crc = utils.compute_crc(chunk)
                crc_matched = computed_crc == read_crc
                if self.check_crc == CrcCheck.ENABLED and not crc_matched:
                    raise FitCRCError('invalid FIT header CRC')

            chunk += extra_chunk

        proto_ver = (proto_ver >> 4, proto_ver & ((1 << 4) - 1))
        profile_ver = (int(profile_ver / 100), int(profile_ver % 100))

        # update state
        self._header = records.FitHeader(
            header_size=header_size,
            proto_ver=proto_ver,
            profile_ver=profile_ver,
            body_size=body_size,
            crc=read_crc,
            crc_matched=crc_matched,
            chunk=self._keep_chunk(chunk))
        self._body_bytes_left = body_size

        if self._processor:
            self._processor.on_header(self, self._header)

    def _read_crc(self):
        computed_crc = self._crc
        chunk, read_crc = self._read_struct('<H')

        if self.check_crc == CrcCheck.ENABLED and computed_crc != read_crc:
            raise FitCRCError()

        crc_obj = records.FitCRC(
            read_crc,
            computed_crc == read_crc,
            self._keep_chunk(chunk))

        if self._processor:
            self._processor.on_crc(self, crc_obj)

        return crc_obj

    def _read_record(self):
        # read header
        chunk = self._read_bytes(1)
        if chunk[0] & 0x80:  # bit 7: compressed timestamp?
            record_header = RecordHeader(
                False,                  # is_definition
                False,                  # is_developer_data
                (chunk[0] >> 5) & 0x3,  # local_mesg_num; bits 5-6
                chunk[0] & 0x1f)        # time_offset; bits 0-4
        else:
            record_header = RecordHeader(
                bool(chunk[0] & 0x40),  # is_definition; bit 6
                bool(chunk[0] & 0x20),  # is_developer_data; bit 5
                chunk[0] & 0xf,         # local_mesg_num; bits 0-3
                None)                   # time_offset

        # read record payload
        if record_header.is_definition:
            message = self._read_definition_message(chunk, record_header)
        else:
            message = self._read_data_message(chunk, record_header)

            if message.mesg_type is not None:
                if message.mesg_type.mesg_num == profile.MESG_NUM_DEVELOPER_DATA_ID:
                    self._add_dev_data_id(message)
                elif message.mesg_type.mesg_num == profile.MESG_NUM_FIELD_DESCRIPTION:
                    self._add_dev_field_description(message)

        return message

    def _read_definition_message(self, header_chunk, record_header):
        record_chunks = [header_chunk]

        # read the "fixed content" part
        extra_chunk = self._read_bytes(5)
        record_chunks.append(extra_chunk)
        endian = '<' if not extra_chunk[1] else '>'
        global_mesg_num, num_fields = struct.unpack(endian + '2xHB',
                                                    extra_chunk)

        # get global message's declaration from our profile if any
        mesg_type = profile.MESSAGE_TYPES.get(global_mesg_num)

        field_unpacker = struct.Struct(endian + '3B')
        field_defs = []
        dev_field_defs = []

        # read field definitions
        for idx in range(num_fields):
            extra_chunk = self._read_bytes(field_unpacker.size)
            record_chunks.append(extra_chunk)

            field_def_num, field_size, base_type_num = \
                field_unpacker.unpack(extra_chunk)

            field = mesg_type.fields.get(field_def_num) if mesg_type else None
            base_type = types.BASE_TYPES.get(
                base_type_num, types.BASE_TYPE_BYTE)

            if (field_size % base_type.size) != 0:
                # should we fall back to byte encoding instead?
                raise FitParseError(
                    self._chunk_offset,
                    f'invalid field size {field_size} for type ' +
                    f'{base_type.name} (expected a multiple of ' +
                    f'{base_type.size})')

            # if the field has components that are accumulators,
            # start recording their accumulation at 0
            if field and field.components:
                for component in field.components:
                    if component.accumulate:
                        accumulators = \
                            self._accumulators.setdefault(global_mesg_num, {})
                        accumulators[component.def_num] = 0

            field_defs.append(types.FieldDefinition(
                field, field_def_num, base_type, field_size))

        # read developer field definitions if any
        if record_header.is_developer_data:
            # read the number of developer fields definitions that follow
            extra_chunk = self._read_bytes(1)
            record_chunks.append(extra_chunk)
            num_dev_fields = extra_chunk[0]

            # read field definitions
            for idx in range(num_dev_fields):
                extra_chunk = self._read_bytes(field_unpacker.size)
                record_chunks.append(extra_chunk)

                field_def_num, field_size, dev_data_index = \
                    field_unpacker.unpack(extra_chunk)

                field = self._get_dev_type(
                    record_header.local_mesg_num, global_mesg_num,
                    dev_data_index, field_def_num)

                dev_field_defs.append(types.DevFieldDefinition(
                    field, dev_data_index, field_def_num, field_size))

        def_mesg = records.FitDefinitionMessage(
            record_header.is_developer_data,
            record_header.local_mesg_num,
            record_header.time_offset,
            mesg_type,
            global_mesg_num,
            endian,
            field_defs,
            dev_field_defs,
            self._keep_chunk(record_chunks))

        # According to FIT protocol's specification (section 4.8.3), it is ok to
        # redefine message types
        self._local_mesg_defs[record_header.local_mesg_num] = def_mesg

        return def_mesg

    def _read_data_message(self, header_chunk, record_header):
        record_chunks = [header_chunk]

        try:
            def_mesg = self._local_mesg_defs[record_header.local_mesg_num]
        except KeyError:
            raise FitParseError(
                self._chunk_offset,
                f'local message {record_header.local_mesg_num} not defined')

        extra_chunks, raw_values = self._read_data_message_raw_values(def_mesg)
        record_chunks.extend(extra_chunks)
        message_fields = []

        for field_def, raw_value in zip(def_mesg.all_field_defs, raw_values):

            field, parent_field = field_def.field, None
            if field:
                field, parent_field = self._resolve_subfield(
                    field, def_mesg, raw_values)

                # resolve component fields
                if field.components:
                    # special case for hr.event_timestamp_12
                    is_hr_event_timestamp_12 = (
                        def_mesg.global_mesg_num == profile.MESG_NUM_HR and
                        not field_def.is_dev and
                        field_def.def_num == profile.FIELD_NUM_HR_EVENT_TIMESTAMP_12)

                    for component in field.components:
                        # render its raw value
                        try:
                            cmp_raw_value = component.render(raw_value)
                        except ValueError:
                            continue

                        # apply accumulated value
                        if component.accumulate and cmp_raw_value is not None:
                            accumulator = self._accumulators[
                                def_mesg.global_mesg_num]

                            cmp_raw_value = self._apply_compressed_accumulation(
                                cmp_raw_value,
                                accumulator[component.def_num],
                                component.bits)

                            accumulator[component.def_num] = cmp_raw_value

                        # apply scale and offset from component, not from the
                        # dynamic field as they may differ
                        cmp_raw_value = self._apply_scale_offset(
                            component, cmp_raw_value)

                        # extract the component's dynamic field from def_mesg
                        cmp_field = def_mesg.mesg_type.fields[component.def_num]

                        # resolve a possible subfield
                        cmp_field, cmp_parent_field = self._resolve_subfield(
                            cmp_field, def_mesg, raw_values)
                        cmp_value = cmp_field.render(cmp_raw_value)

                        # special case: hr.event_timestamp_12
                        if is_hr_event_timestamp_12:
                            assert self._hr_start_timestamp > 0
                            cmp_value += self._hr_start_timestamp

                        message_fields.append(types.FieldData(
                            None,              # field_def
                            cmp_field,         # field
                            cmp_parent_field,  # parent_field
                            cmp_value,         # value
                            cmp_raw_value))    # raw_value

                decoded_value = self._apply_scale_offset(
                    field, field.render(raw_value))
            else:
                decoded_value = raw_value

            # specifics
            if (field_def.def_num == profile.FIELD_NUM_TIMESTAMP and
                    raw_value is not None):
                self._last_timestamp = decoded_value
                # update compressed timestamp field
                self._compressed_ts_accumulator = raw_value
            elif (def_mesg.global_mesg_num == profile.MESG_NUM_HR and
                    not field_def.is_dev and
                    field_def.def_num == profile.FIELD_NUM_HR_EVENT_TIMESTAMP):
                # hr.event_timestamp_12 fields are accumulated from an initial
                # hr.event_timestamp value
                # assert self._last_timestamp > 0
                self._hr_start_timestamp = self._last_timestamp

            message_fields.append(types.FieldData(
                field_def,      # field_def
                field,          # field
                parent_field,   # parent_field
                decoded_value,  # value
                raw_value))     # raw_value

        # apply timestamp field if we got a header
        if record_header.time_offset is not None:
            ts_value = self._apply_compressed_accumulation(
                record_header.time_offset, self._compressed_ts_accumulator, 5)

            self._compressed_ts_accumulator = ts_value

            message_fields.append(types.FieldData(
                None,                                           # field_def
                profile.FIELD_TYPE_TIMESTAMP,                   # field
                None,                                           # parent_field
                profile.FIELD_TYPE_TIMESTAMP.render(ts_value),  # value
                ts_value))                                      # raw_value

        # apply data processors
        if self._processor:
            for field_data in message_fields:
                self._processor.on_process_type(self, field_data)
                self._processor.on_process_field(self, field_data)
                self._processor.on_process_unit(self, field_data)

        data_message = records.FitDataMessage(
            record_header.is_developer_data,
            record_header.local_mesg_num,
            record_header.time_offset,
            def_mesg,
            message_fields,
            self._keep_chunk(record_chunks))

        if self._processor:
            self._processor.on_process_message(self, data_message)

        # keep track of the last file_id message
        if def_mesg.global_mesg_num == profile.MESG_NUM_FILE_ID:
            self._file_id = data_message

        return data_message

    def _read_data_message_raw_values(self, def_mesg):
        raw_values = []
        record_chunks = []

        for field_def in def_mesg.all_field_defs:
            base_type = field_def.base_type

            # struct format to read "[N]" base types
            unpacker = struct.Struct(
                def_mesg.endian +
                str(int(field_def.size / base_type.size)) +
                base_type.fmt)

            # read the chunk
            chunk = self._read_bytes(unpacker.size)
            record_chunks.append(chunk)

            # extract the raw value
            raw_value = unpacker.unpack(chunk)

            if base_type.identifier == types.BASE_TYPE_BYTE.identifier:
                raw_value = base_type.parse(raw_value)
            elif len(raw_value) > 1:
                # If the field returns with a tuple of values it's definitely an
                # oddball, but we'll parse it on a per-value basis. If it's a
                # byte type, treat the tuple as a single value
                raw_value = tuple(base_type.parse(v) for v in raw_value)
            else:
                # Otherwise, just scrub the singular value
                raw_value = base_type.parse(raw_value[0])

            raw_values.append(raw_value)

        return record_chunks, raw_values

    def _read_struct(self, fmt, *, endian=None):
        assert fmt
        if endian:
            fmt = endian + fmt

        unpacker = struct.Struct(fmt)
        if unpacker.size <= 0:
            raise ValueError(f'invalid struct format "{fmt}"')

        chunk = self._read_bytes(unpacker.size)

        return (chunk, ) + unpacker.unpack(chunk)

    def _read_bytes(self, size):
        if size <= 0:
            raise ValueError('size')

        chunk = utils.blocking_read(self._fd, size)
        chunk_size = 0 if not chunk else len(chunk)
        if chunk_size != size:
            raise FitEOFError(size, chunk_size, self._read_offset)

        if chunk:
            if self.check_crc != CrcCheck.DISABLED:
                self._crc = utils.compute_crc(chunk, crc=self._crc)
            self._chunk_size += chunk_size
            self._read_offset += chunk_size
            self._read_size += chunk_size

        return chunk

    def _keep_chunk(self, chunk):
        if not self._keep_raw:
            return None

        assert chunk
        assert isinstance(chunk, (list, tuple, bytes))

        if isinstance(chunk, (list, tuple)):
            # *chunk* is a list of chunks
            assert sum(map(lambda x: len(x), chunk)) == self._chunk_size
            return records.FitChunk(
                self._chunk_index, self._chunk_offset, b''.join(chunk))

        else:
            assert len(chunk) == self._chunk_size
            return records.FitChunk(
                self._chunk_index, self._chunk_offset, chunk)

    def _add_dev_data_id(self, message):
        dev_data_index = message.get_field('developer_data_index').raw_value

        try:
            application_id = message.get_field('application_id').raw_value
        except KeyError:
            application_id = None

        # declare/overwrite type
        self._local_dev_types[dev_data_index] = {
            'dev_data_index': dev_data_index,
            'application_id': application_id,
            'fields': {}}

    def _add_dev_field_description(self, message):
        dev_data_index = message.get_field('developer_data_index').raw_value
        if dev_data_index not in self._local_dev_types:
            raise FitParseError(
                self._chunk_offset,
                f'dev_data_index {dev_data_index} not defined')

        field_def_num = message.get_field('field_definition_number').raw_value
        base_type_id = message.get_field('fit_base_type_id').raw_value
        field_name = message.get_field('field_name').raw_value

        try:
            units = message.get_field('units').raw_value
        except KeyError:
            units = None

        try:
            native_field_num = message.get_field('native_field_num')
            native_field_num = native_field_num.raw_value
        except KeyError:
            native_field_num = None

        fields = self._local_dev_types[int(dev_data_index)]['fields']

        # declare/overwrite type
        fields[field_def_num] = types.DevField(
            dev_data_index, field_name, field_def_num,
            types.BASE_TYPES[base_type_id], units, native_field_num)

    def _get_dev_type(self, local_mesg_num, global_mesg_num, dev_data_index,
                      field_def_num):
        if dev_data_index not in self._local_dev_types:
            raise FitParseError(
                self._chunk_offset,
                f'dev_data_index {dev_data_index} not defined ' +
                f'(looking up for field {field_def_num}; ' +
                f'local_mesg_num: {local_mesg_num}; ' +
                f'global_mesg_num: {global_mesg_num})')

        try:
            return self._local_dev_types[dev_data_index]['fields'][field_def_num]
        except KeyError:
            raise FitParseError(
                self._chunk_offset,
                f'no such field {field_def_num} for dev_data_index ' +
                f'{dev_data_index} (local_mesg_num: {local_mesg_num}; ' +
                f'global_mesg_num: {global_mesg_num})')

    @staticmethod
    def _resolve_subfield(field, def_mesg, raw_values):
        # resolve into (field, parent) ie (subfield, field) or (field, none)
        if field.subfields:
            for sub_field in field.subfields:
                # go through reference fields for this sub field
                for ref_field in sub_field.ref_fields:
                    # go through field defs AND their raw values
                    for field_def, raw_value in zip(
                            def_mesg.field_defs, raw_values):
                        # if there's a definition number AND raw value match on
                        # the reference field, then we return this subfield
                        if (field_def.def_num == ref_field.def_num and
                                ref_field.raw_value == raw_value):
                            return sub_field, field

        return field, None

    @staticmethod
    def _apply_compressed_accumulation(raw_value, accumulation, num_bits):
        max_value = 1 << num_bits
        max_mask = max_value - 1
        base_value = raw_value + (accumulation & ~max_mask)

        if raw_value < (accumulation & max_mask):
            base_value += max_value

        return base_value

    @classmethod
    def _apply_scale_offset(cls, field, raw_value):
        # apply numeric transformations (scale + offset)
        if isinstance(raw_value, tuple):
            # contains multiple values, apply transformations to all of them
            return tuple(cls._apply_scale_offset(field, x) for x in raw_value)
        elif isinstance(raw_value, (int, float)):
            if field.scale:
                raw_value = float(raw_value) / field.scale
            if field.offset:
                raw_value = raw_value - field.offset

        return raw_value
