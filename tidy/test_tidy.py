import re
import unittest
import tidy


class TidyTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TidyTestCase, self).__init__(*args, **kwargs)
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
        return (doc1, doc2, doc3)

    def test_badOptions(self):
        badopts = [{'foo': 1}, {'indent': '---'}, {'indent_spaces': None}]
        for opts in badopts:
            self.assertRaises(
                tidy.TidyLibError,
                tidy.parseString,
                self.input2,
                **opts
            )

    def test_encodings(self):
        foo = file('foo.htm').read().decode('utf8').encode('ascii',
                                                           'xmlcharrefreplace')
        doc1u = tidy.parseString(foo, input_encoding='ascii',
                                 output_encoding='latin1')
        self.assertTrue(str(doc1u).find('\xe9') >= 0)
        doc2u = tidy.parseString(foo, input_encoding='ascii',
                                 output_encoding='utf8')
        self.assertTrue(str(doc2u).find('\xc3\xa9') >= 0)

    def test_errors(self):
        doc1, doc2, doc3 = self.defaultDocs()
        for doc in [doc1, doc2, doc3]:
            str(getattr(doc, 'errors'))
            self.assertEquals(doc1.errors[0].line, 1)

    def test_options(self):
        options = dict(add_xml_decl=1, show_errors=1, newline='CR',
                       output_xhtml=1)
        doc1 = tidy.parseString(self.input1, **options)
        found = re.search(r'//<![[]CDATA[[]\W+1>2\W+//]]>', str(doc1),
                          re.MULTILINE)
        self.assertTrue(found)
        doc2 = tidy.parseString("<Html>", **options)
        self.assertTrue(str(doc2).startswith('<?xml'))
        self.assertFalse(len(doc2.errors) == 0)
        self.assertTrue(str(doc2).find('\n') < 0)
        doc3 = tidy.parse('foo.htm', char_encoding='utf8',
                          alt_text='foo')
        self.assertTrue(str(doc3).find('alt="foo"') >= 0)
        self.assertTrue(str(doc3).find('\xc3\xa9') >= 0)

    def test_parse(self):
        doc1, doc2, doc3 = self.defaultDocs()
        self.assertTrue(str(doc1).find('</html>') >= 0)
        self.assertTrue(str(doc2).find('</html>') >= 0)
        self.assertTrue(str(doc3).find('</html>') >= 0)
