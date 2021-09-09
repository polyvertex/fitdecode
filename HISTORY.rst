.. :changelog:

==========
Change Log
==========


v0.8.0 (2021-09-09)
===================

* `FitReader` gets the ``error_handling`` argument to be less strict on
  malformed files (issues #13, #16, #18)
* FIT SDK profile upgraded to v21.60
* Minor corrections, improvements and cleanup on code and documentation


v0.7.0 (2020-10-04)
===================

* Compatibility with Apple Watch improved (issue #10)
* FIT SDK profile upgraded to v21.38
* ``generate_profile`` utility now supports recent SDK file structure
* Minor improvements and cleanup on code and documentation


v0.6.0 (2019-11-02)
===================

* Added `FitReader.last_timestamp` property
* Fixed: `FitReader` was raising `KeyError` instead of `FitParseError` when a
  dev_type was not found
* `FitParseError` message contains more details upon malformed file in some
  cases
* FIT SDK profile upgraded to v21.16
* README's usage example slightly improved


v0.5.0 (2019-04-11)
===================

* Added `fitdecode.DataProcessorBase` class
* ``check_crc`` - the parameter to `fitdecode.FitReader`'s constructor - can now
  be either "enabled", "read-only" or "disabled" (issue #1)
* Minor speed improvements


v0.4.0 (2019-04-10)
===================

* Added `fitdecode.FitDataMessage.has_field`
* `fitdecode.FitDataMessage.get_fields` is now a generator
* `fitdecode.FitDataMessage.get_values` is now a generator
* `fitdecode.DefaultDataProcessor` now converts ``hr.event_timestamp`` values
  that were populated from ``hr.event_timestamp_12`` components to
  `datetime.datetime` objects for convenience
* ``fitjson`` and ``fittxt`` utilities:
  * Added support for input files with Unicode characters
  * Still write output file even if an error occurred while parsing FIT file
* Fixed handling of some FIT fields that are both scaled and components.
  See https://github.com/dtcooper/python-fitparse/issues/84
* Improved support for malformed FIT files.
  See https://github.com/dtcooper/python-fitparse/issues/62
* ``generate_profile`` utility slightly improved
* Added some unit tests
* Minor improvements and corrections


v0.3.0 (2018-07-27)
===================

* Added `fitdecode.utils.get_mesg_field`
* Added `fitdecode.utils.get_mesg_field_num`
* Minor improvements and corrections


v0.2.0 (2018-07-16)
===================

* Added `FieldData.name_or_num`
* Added `FitDataMessage.get_fields`
* Added `FitDataMessage.get_values`
* Improved `FitDataMessage.get_field` (*idx* arg)
* Improved `FitDataMessage.get_value` (*idx* arg)
* Completed documentation of `FitDataMessage`
* Improved documentation of `FieldData`
* `FitReader`'s internal state is reset as well after a `FitCRC` has been
  yielded (i.e. not only when a FIT header is about to be read), in order to
  avoid incorrect behavior due to malformed FIT stream


v0.1.0 (2018-07-14)
===================

* Added class property ``frame_type`` (read-only) to `FitHeader`, `FitCRC`,
  `FitDefinitionMessage` and `FitDataMessage` (``records`` module) to ease and
  speed up type checking
* Added `FitDataMessage.get_value` method
* ``string`` values with no null byte are still decoded (in full length)
* ``cmd`` directory added to the source code tree for convenience


v0.0.1 (2018-07-08)
===================

* First release


v0.0.0 (2018-05-31)
===================

* Birth!
