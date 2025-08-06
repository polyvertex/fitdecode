=========
fitdecode
=========

.. image:: https://readthedocs.org/projects/fitdecode/badge/?version=latest
    :target: https://fitdecode.readthedocs.io/
    :alt: Latest Docs

.. image:: https://github.com/polyvertex/fitdecode/actions/workflows/python-test.yml/badge.svg
    :target: https://github.com/polyvertex/fitdecode/actions/workflows/python-test.yml
    :alt: python-test


A `FIT <https://developer.garmin.com/fit/overview/>`_ file parsing and decoding
library written in `Python <https://www.python.org/>`_ (``>= 3.6``).


Usage Example
=============

Read a FIT file, frame by frame:

.. code:: python

    import fitdecode

    with fitdecode.FitReader('file.fit') as fit:
        for frame in fit:
            # The yielded frame object is of one of the following types:
            # * fitdecode.FitHeader (FIT_FRAME_HEADER)
            # * fitdecode.FitDefinitionMessage (FIT_FRAME_DEFINITION)
            # * fitdecode.FitDataMessage (FIT_FRAME_DATA)
            # * fitdecode.FitCRC (FIT_FRAME_CRC)

            if frame.frame_type == fitdecode.FIT_FRAME_DATA:
                # Here, frame is a FitDataMessage object.
                # A FitDataMessage object contains decoded values that
                # are directly usable in your script logic.
                print(frame.name)


Command line utilities
----------------------

``fitjson`` command converts a FIT file to JSON:

::

    $ fitjson --pretty -o out_file.json in_file.fit

``fittxt`` command converts a FIT file to human-readable text format convenient
to ease FIT data inspection and debugging::

    $ fittxt -o out_file.txt in_file.fit

Both commands accept a ``--filter`` option (or ``-f``) which can be specified
multiples times::

    $ # include only RECORD messages:
    $ fitjson -f=record -o out_file.json in_file.fit

    $ # exclude FILE_ID and EVENT messages:
    $ fitjson -f=-file_id -f=-event -o out_file.json in_file.fit


Installation
============

fitdecode is available on `PyPI <https://pypi.org/project/fitdecode/>`_::

    $ pip install fitdecode


Or, you can clone fitdecode's `source code repository
<https://github.com/polyvertex/fitdecode>`_ before installing it::

    $ git clone git@github.com:polyvertex/fitdecode.git
    $ cd fitdecode
    $ pip install .


Note that for convenience, directory ``cmd`` located at the root of the project
can safely be added to your ``PATH``, such that fitdecode commands can be called
without the package to be installed.


Overview
========

fitdecode is a non-offensive and incompatible rewrite of the fitparse_ library,
with some improvements and additional features, thread-safety, and efforts to
optimize both speed and memory usage.

Main differences between fitdecode and fitparse:

* fitdecode API is not compatible with fitparse
* fitdecode is faster
* fitdecode allows concurrent reading of multiple streams by being thread-safe,
  in the sense that fitdecode's objects keep their state stored locally
* fitdecode does not discard the FIT header and the CRC footer while reading a
  stream so that client code gets a complete 1:1 representation of the stream
  that is being read
* This also allows client code to easily deal with so-called chained FIT files,
  as per FIT SDK definition (i.e. concatenated FIT files)
* CRC computation and matching are both optional. CRC can be either matched, or
  only computed, or just ignored for faster reading.
* fitdecode offers optional access to records, headers and footers in their
  binary form, so to allow FIT file cutting, stitching and filtering at binary
  level


Why a new library?
==================

A new library has been created instead of just offering to patch fitparse_
because many changes and adds in fitdecode break fitparse's backward
compatibilty and because it allowed more freedom during the development of
fitdecode.


Documentation
=============

Documentation is available at `<https://fitdecode.readthedocs.io/>`_


License
=======

This project is distributed under the terms of the MIT license.
See the `LICENSE.txt <LICENSE.txt>`_ file for details.


Credits
=======

fitdecode is largely based on the generic approach adopted by fitparse_ to
define FIT types and to decode raw values. That includes the module
``profile.py`` and all the classes it refers to, as well as the script
``generate_profile.py``.



.. _fitparse: https://github.com/dtcooper/python-fitparse
