.. :changelog:

==========
Change Log
==========


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
