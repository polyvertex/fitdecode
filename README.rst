=========
fitdecode
=========

A `FIT <http://www.thisisant.com>`_ file parsing and decoding library written in
`Python3 <https://www.python.org/>`_ (3.6+ only).


Usage Example
=============

Read a FIT file, chunk by chunk:

.. code:: python

    import fitdecode

    with fitdecode.FitReader(src_file) as fit:
        for record in fit:
            # The yielded *record* object has one of the following types:
            # * fitdecode.FitHeader
            # * fitdecode.FitDefinitionMessage
            # * fitdecode.FitDataMessage
            # * fitdecode.FitCrc
            #
            # A fitdecode.FitDataMessage object contains decoded values that are
            # directly usable in your script logic.
            pass


Installation
============

fitdecode is available on `PyPI <https://pypi.org/project/fitdecode/>`_::

    $ pip install fitdecode


Or you can clone fitdecode's `source code repository
<https://github.com/polyvertex/fitdecode>`_ before installing it::

    $ git clone git@github.com:polyvertex/fitdecode.git
    $ cd fitdecode
    $ python setup.py test     # optional step to run unit tests
    $ python setup.py install


Overview
========

fitdecode is a non offensive and incompatible rewrite of the fitparse_ library,
with some improvements and additional features, as well as efforts made to
optimize both speed and memory usage.

Main differences between fitdecode and fitparse:

* fitdecode requires Python version 3.6 or greater

* fitdecode is thread-safe in the sense that it does not perform write access
  to any global variable, and that the objects keep their state storage locally

* fitdecode highest level interfaces, FitReader and FitDecoder, are not
  compatible with fitparse's FitFile

* fitdecode does not discard the FIT header and the CRC footer while iterating
  a file, which allow to get a complete 1:1 representation of the file that is
  being read

* This also allows the client to easily deal with so-called chained FIT files,
  as per FIT SDK definition (i.e. concatenated FIT files)

* fitdecode offers optional access to records, headers and footers in their
  binary form, to allow FIT file cutting, stitching and filtering at binary
  level

* fitdecode offers a higher level of abstraction (``decoder.py`` module) to
  allow data processing and consolidation at file level.

  One typical use case example is the ``hr`` messages that are appended by
  Garmin watches (at least) to a "swim" activity file during the post-activity
  synchronization step, when the HRM strap sends its data to the watch.

  The content of these ``hr`` messages (heart rate) has to be merged to the
  ``record`` messages of the activity, before being erased from the messages
  list.


Why a new library?
==================

It has been decided to create a new library instead of just offering to patch
fitparse_ because many changes and adds in fitdecode break fitparse's backward
compatibilty and because it allowed more liberty during the development of
fitdecode.


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
