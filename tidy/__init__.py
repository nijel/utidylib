"""The Tidy wrapper.
I am the main interface to TidyLib. This package supports processing HTML with
Tidy, with all the options that the tidy command line supports.

For more information on the tidy options, see the reference. These options can
be given as keyword arguments to parse and parseString, by changing dashes (-)
to underscores(_).

For example:

>>> import tidy
>>> options = dict(output_xhtml=1, add_xml_decl=1, indent=1, tidy_mark=0)
>>> print tidy.parseString('<Html>Hello Tidy!', **options)
<?xml version="1.0" encoding="us-ascii"?>
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

For options like newline and output_encoding, which must be set to one of a
fixed number of choices, you can provide either the numeric or string version
of the choice; so both tidy.parseString('<HTML>foo</html>', newline=2) and
tidy.parseString('<HTML>foo</html>', newline='CR') do the same thing.  

There are no plans to support other features of TidyLib, such as document-tree
traversal, since Python has several quality DOM implementations. (The author
uses Twisted's implementation, twisted.web.microdom).
"""

try:
    dict(x=1)
except TypeError:
    raise ImportError("Python 2.3 or later is required to import this library.")

__all__ = ['error', 'lib']

from tidy.lib import parse, parseString
from tidy.error import *

