=========
fitdecode
=========

A `FIT <http://www.thisisant.com>`_ file parsing and decoding library written in
`Python3 <https://www.python.org/>`_ (3.6+ only).


Usage Example
=============

Read a FIT file, frame by frame:

.. code:: python

    import fitdecode

    with fitdecode.FitReader(src_file) as fit:
        for frame in fit:
            # The yielded *frame* object is of one of the following types:
            # * fitdecode.FitHeader
            # * fitdecode.FitDefinitionMessage
            # * fitdecode.FitDataMessage
            # * fitdecode.FitCRC
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

* fitdecode allows concurrent reading of multiple files by being thread-safe, in
  the sense that fitdecode's objects keep their state stored locally

* fitdecode high-level interfaces are not compatible with fitparse's FitFile

* fitdecode does not discard the FIT header and the CRC footer while iterating
  a file, which allow to get a complete 1:1 representation of the file that is
  being read

* This also allows the client to easily deal with so-called chained FIT files,
  as per FIT SDK definition (i.e. concatenated FIT files)

* fitdecode offers optional access to records, headers and footers in their
  binary form, to allow FIT file cutting, stitching and filtering at binary
  level


Why a new library?
==================

A new library has been created instead of just offering to patch fitparse_
because many changes and adds in fitdecode break fitparse's backward
compatibilty and because it allowed more freedom during the development of
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
