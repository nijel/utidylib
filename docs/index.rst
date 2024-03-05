Welcome to uTidylib's documentation!
====================================

.. automodule:: tidy

.. autofunction:: parse

.. autofunction:: parseString

.. autoclass:: Document
   :members:

.. autoclass:: ReportItem
   :members:

.. autoexception:: TidyLibError

.. autoexception:: InvalidOptionError

.. autoexception:: OptionArgError

Installing
==========

To use uTidylib, you need to have HTML tidy library installed.
Check <http://www.html-tidy.org/> for instructions how to obtain it.

Once you have installed the library, install uTidylib:

.. code-block:: sh

    pip install uTidylib

Contributing
============

You are welcome to contribute on GitHub, we use it for source code management,
issue tracking and patches submission, see <https://github.com/nijel/utidylib>.

Running testsuite
=================

The testsuite can be exececuted using pytest:

.. code-block:: sh

    pytest tidy

Building documentation
======================

To build the doc, just run:

.. code-block:: sh

    make -C docs html

This requires that you have Sphinx installed.

The API documentation will be built in the :file:`docs/_build/html/` directory.

License
=======

.. include:: ../LICENSE

.. include:: ../CHANGES.rst

History
=======

This is fork of the original uTidylib with permission with original author.
Originally it incorporated patches from Debian and other distributions, now it
also brings compatibility with recent html-tidy versions and works with Python 3.

The original source code is still available at https://github.com/xdissent/utidylib/.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
