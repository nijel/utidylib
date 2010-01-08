import re
from twisted.trial import unittest
import tidy

class TidyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        foo = u'''<html>
    <h1>woot</h1>
    <hr>
    <img src=\'asdfasdf\'>
    <p>\N{LATIN SMALL LETTER E WITH ACUTE}
<!-- hhmts end -->
  </body>
</html>
'''.encode('utf8')
        file('foo.htm', 'w').write(foo)
        self.input1 = "<html><script>1>2</script>"
        self.input2 = "<html>\n" + "<p>asdkfjhasldkfjhsldjas\n" * 100
    def defaultDocs(self):
        doc1 = tidy.parseString(self.input1)
        doc2 = tidy.parseString(self.input2)
        doc3 = tidy.parse("foo.htm")
        doc4 = tidy.parse("bar.htm") # doesn't exist
        return (doc1, doc2, doc3, doc4)
    def test_badOptions(self):
        badopts = [{'foo': 1}, {'indent': '---'}, {'indent_spaces': None}]
        for dct in badopts:
            try:
                tidy.parseString(self.input2, **dct)
            except tidy.TidyLibError:
                pass
            else:
                self.fail("Invalid option %s should have raised an error" %
                          repr(dct))
    def test_encodings(self):
        foo = file('foo.htm').read().decode('utf8').encode('ascii', 
                                                           'xmlcharrefreplace')
        doc1u = tidy.parseString(foo, input_encoding='ascii',
                                 output_encoding='latin1')
        self.failUnless(str(doc1u).find('\xe9')>=0)
        doc2u = tidy.parseString(foo, input_encoding='ascii',
                                 output_encoding='utf8')
        self.failUnless(str(doc2u).find('\xc3\xa9')>=0)
    def test_errors(self):
        doc1, doc2, doc3, doc4 = self.defaultDocs()
        for doc in [doc1, doc2, doc3]:
            str(getattr(doc, 'errors'))
            self.assertEquals(doc1.errors[0].line, 1)
    def test_options(self):
        options = dict(add_xml_decl=1, show_errors=1, newline='CR', 
                       output_xhtml=1)
        doc1 = tidy.parseString(self.input1, **options)
        found = re.search('//<![[]CDATA[[]\W+1>2\W+//]]>', str(doc1),
                          re.MULTILINE)
        self.failUnless(found)
        doc2 = tidy.parseString("<Html>", **options)
        self.failUnless(str(doc2).startswith('<?xml'))
##        self.failIf(len(doc2.errors)>1) # FIXME - tidylib doesn't
##                                        # support this?
        self.failUnless(str(doc2).find('\n')<0)
        doc3 = tidy.parse('foo.htm', char_encoding='utf8', 
                          alt_text='foo')
        self.failUnless(str(doc3).find('alt="foo"')>=0)
        self.failUnless(str(doc3).find('\xc3\xa9')>=0)
    def test_parse(self):
        doc1, doc2, doc3, doc4 = self.defaultDocs()
        self.failUnless(str(doc1).find('</html>') >=0)
        self.failUnless(str(doc2).find('</html>') >= 0)
        self.failUnless(str(doc3).find('</html>') >= 0)
