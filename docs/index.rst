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

Contributing
============

You are welcome to contribute on GitHub, we use it for source code management,
issue tracking and patches submission, see <https://github.com/nijel/utidylib>.

Running testsuite
=================

The testsuite can be exececuted using both py.test or setuptools, choose whatever approach you prefer:

.. code-block:: sh

    ./setup.py test
    py.test tidy

Building documentation
======================

To build the doc, just run:

.. code-block:: sh

    make -C docs html

This requires that you have Sphinx installed.

The API documentation will be built in the :file:`docs/_build/html/` directory.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

