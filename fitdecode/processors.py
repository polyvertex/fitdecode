# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

import datetime

from .utils import scrub_method_name

__all__ = ['FitFileDataProcessor', 'FIT_UTC_REFERENCE']


#: Datetimes (uint32) represent seconds since this FIT_UTC_REFERENCE
#: (timestamp for UTC 00:00 Dec 31 1989)
FIT_UTC_REFERENCE = 631065600

#: UNIX timestamp: Tue., July 4, 1978 9:24:16 PM
FIT_DATETIME_MIN = 0x10000000


class FitFileDataProcessor:
    """
    Processor to change raw values to more comfortable ones.

    Uses method cache to speed up the processing - reuse the object if used
    multiple times.
    """

    # TODO: Document API
    # Functions that will be called to do the processing:
    # def run_type_processor(field_data)
    # def run_field_processor(field_data)
    # def run_unit_processor(field_data)
    # def run_message_processor(data_message)

    # By default, the above functions call these functions if they exist:
    # def process_type_<type_name> (field_data)
    # def process_field_<field_name> (field_data) -- can be unknown_DD but NOT recommended
    # def process_units_<unit_name> (field_data)
    # def process_message_<mesg_name / mesg_type_num> (data_message)

    def __init__(self):
        # used to memoize scrubbed methods
        self._method_cache = {}

    def run_type_processor(self, field_data):
        self._run_processor('process_type_' + field_data.type.name, field_data)

    def run_field_processor(self, field_data):
        self._run_processor('process_field_' + field_data.name, field_data)

    def run_unit_processor(self, field_data):
        if field_data.units:
            self._run_processor('process_units_' + field_data.units, field_data)

    def run_message_processor(self, data_message):
        self._run_processor(
            'process_message_' + data_message.def_mesg.name, data_message)

    def process_type_bool(self, field_data):
        if field_data.value is not None:
            field_data.value = bool(field_data.value)

    def process_type_date_time(self, field_data):
        if (field_data.value is not None and
                field_data.value >= FIT_DATETIME_MIN):
            field_data.value = datetime.datetime.fromtimestamp(
                FIT_UTC_REFERENCE + field_data.value,
                datetime.timezone.utc)
            field_data.units = None  # units were 's', set to None

    def process_type_local_date_time(self, field_data):
        if field_data.value is not None:
            # This value was created on the device using its local timezone.
            # Unless we know that timezone, this value won't be correct.
            # However, if we assume UTC, at least it'll be consistent.
            field_data.value = datetime.datetime.utcfromtimestamp(
                FIT_UTC_REFERENCE + field_data.value)
            field_data.units = None

    def process_type_localtime_into_day(self, field_data):
        if field_data.value is not None:
            m, s = divmod(field_data.value, 60)
            h, m = divmod(m, 60)
            field_data.value = datetime.time(h, m, s)
            field_data.units = None

    def _run_processor(self, method_name, data):
        method = self._get_scrubbed_method(method_name)
        if method is None:
            return
        method(data)

    def _get_scrubbed_method(self, method_name):
        method = self._method_cache.get(method_name, False)
        if method is not False:
            return method

        scrubbed_method_name = scrub_method_name(method_name)
        method = getattr(self, scrubbed_method_name, None)

        self._method_cache[method_name] = method

        return method


class StandardUnitsDataProcessor(FitFileDataProcessor):
    def run_field_processor(self, field_data):
        """
        Convert all '*_speed' fields using 'process_field_speed'
        All other units will use the default method.
        """
        if field_data.name.endswith("_speed"):
            self.process_field_speed(field_data)
        else:
            super().run_field_processor(field_data)

    def process_field_distance(self, field_data):
        if field_data.value is not None:
            field_data.value /= 1000.0
        field_data.units = 'km'

    def process_field_speed(self, field_data):
        if field_data.value is not None:
            field_data.value *= 60.0 * 60.0 / 1000.0
        field_data.units = 'km/h'

    def process_units_semicircles(self, field_data):
        if field_data.value is not None:
            field_data.value *= 180.0 / (2 ** 31)
        field_data.units = 'deg'


_DEFAULT_PROCESSOR = FitFileDataProcessor()


def get_default_processor():
    """Default, shared instance of processor (due to the method cache)"""
    return _DEFAULT_PROCESSOR
