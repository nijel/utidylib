uTidylib
========

.. image:: https://travis-ci.org/nijel/utidylib.svg?branch=master
    :target: https://travis-ci.org/nijel/utidylib
    :alt: Build Status

.. image:: https://codecov.io/gh/nijel/utidylib/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/nijel/utidylib
    :alt: Coverage Status

.. image:: https://readthedocs.org/projects/utidylib/badge/?version=latest
    :target: http://utidylib.readthedocs.org/en/latest/
    :alt: Documentation


This is fork of uTidylib with permission with original author. Originally it
incorporated patches from Debian and other distributions, now it also brings
compatibility with recent html-tidy versions and works with Python 3.

Unfortunatelly this version is not released to PyPI as there is currently no
working process to take over maintainership there and original uploader (who is
different from original library author) is not reachable.

This is uTidylib, the Python wrapper for the HTML cleaning
library named TidyLib. It supports both original Tidy <http://tidy.sf.net> and new
HTML5 enabled Tidy <http://www.html-tidy.org/>.

Once installed, there are two ways to get help.  The simplest is:

.. code-block:: sh

    $ python
    >>> import tidy
    >>> help(tidy)
    . . .

Then, of course, there's the API documentation, which
is available at <http://utidylib.readthedocs.io/en/latest/>.

10 Second Tutorial
------------------

.. code-block:: python

    >>> import tidy
    >>> print(tidy.parseString(
    ...     '<Html>Hello Tidy!',
    ...     output_xhtml=1, add_xml_decl=1, indent=1, tidy_mark=0,
    ...     doctype='transitional'
    ... ))
    <?xml version="1.0"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title></title>
      </head>
      <body>
        Hello Tidy!
      </body>
    </html>


Good luck!
