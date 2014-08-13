from __future__ import unicode_literals
import re
import unittest
import tidy
import six
import os.path

DATA_STORAGE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'test_data'
)


class TidyTestCase(unittest.TestCase):
    input1 = "<html><script>1>2</script>"
    input2 = "<html>\n" + "<p>asdkfjhasldkfjhsldjas\n" * 100
    test_file = os.path.join(DATA_STORAGE, 'test.html')

    def default_docs(self):
        doc1 = tidy.parseString(self.input1)
        doc2 = tidy.parseString(self.input2)
        doc3 = tidy.parse(self.test_file)
        return (doc1, doc2, doc3)

    def test_bad_options(self):
        badopts = [{'foo': 1}, {'indent': '---'}, {'indent_spaces': None}]
        for opts in badopts:
            self.assertRaises(
                tidy.TidyLibError,
                tidy.parseString,
                self.input2,
                **opts
            )

    def test_encodings(self):
        text = open(self.test_file, 'rb').read().decode('utf8').encode(
            'ascii', 'xmlcharrefreplace'
        )
        doc1u = tidy.parseString(text, input_encoding='ascii',
                                 output_encoding='latin1')
        self.assertTrue(str(doc1u).find(b'\xe9') >= 0)
        doc2u = tidy.parseString(text, input_encoding='ascii',
                                 output_encoding='utf8')
        self.assertTrue(str(doc2u).find(b'\xc3\xa9') >= 0)

    def test_errors(self):
        for doc in self.default_docs():
            self.assertEquals(doc.errors[0].line, 1)

    def test_nonexisting(self):
        doc = tidy.parse(os.path.join(DATA_STORAGE, 'missing.html'))
        self.assertEquals(str(doc), '')
        self.assertTrue('missing.html' in doc.errors[0].message)
        self.assertEquals(doc.errors[0].severity, 'E')
        self.assertTrue(str(doc.errors[0]).startswith('Error'))

    def test_options(self):
        doc1 = tidy.parseString(
            self.input1,
            add_xml_decl=1, show_errors=1, newline='CR', output_xhtml=1
        )
        found = re.search(r'//<![[]CDATA[[]\W+1>2\W+//]]>', str(doc1),
                          re.MULTILINE)
        self.assertTrue(found)
        doc2 = tidy.parseString(
            "<Html>",
            add_xml_decl=1, show_errors=1, newline='CR', output_xhtml=1
        )
        self.assertTrue(str(doc2).startswith('<?xml'))
        self.assertFalse(len(doc2.errors) == 0)
        self.assertTrue(str(doc2).find('\n') < 0)
        doc3 = tidy.parse(self.test_file, char_encoding='utf8',
                          alt_text='foo')
        self.assertTrue(str(doc3).find(b'alt="foo"') >= 0)
        self.assertTrue(str(doc3).find(b'\xc3\xa9') >= 0)

    def test_parse(self):
        doc1, doc2, doc3 = self.default_docs()
        self.assertTrue(str(doc1).find('</html>') >= 0)
        self.assertTrue(str(doc2).find('</html>') >= 0)
        self.assertTrue(str(doc3).find('</html>') >= 0)

    def test_big(self):
        text = 'x' * 16384
        doc = tidy.parseString('<html><body>{0}</body></html>'.format(text))
        self.assertTrue(text in str(doc))

    def test_write(self):
        doc = tidy.parseString(self.input1)
        handle = six.BytesIO()
        doc.write(handle)
        self.assertEquals(str(doc), handle.getvalue())

    def test_errors(self):
        doc = tidy.parseString(self.input1)
        for error in doc.errors:
            self.assertTrue(str(error).startswith('line'))
