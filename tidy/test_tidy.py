from __future__ import unicode_literals
import unittest
import os.path

import six

import tidy
import tidy.lib


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
        doc3 = tidy.parse(self.test_file, char_encoding='ascii')
        return (doc1, doc2, doc3)

    def test_bad_options(self):
        badopts = [{'foo': 1}]
        for opts in badopts:
            with self.assertRaisesRegexp(
                tidy.InvalidOptionError, 'not a valid Tidy option'
            ):
                tidy.parseString(self.input2, **opts)

    def test_bad_option_values(self):
        badopts = [{'indent': '---'}, {'indent_spaces': None}]
        for opts in badopts:
            with self.assertRaisesRegexp(
                tidy.OptionArgError, 'missing or malformed argument'
            ):
                tidy.parseString(self.input2, **opts)

    def test_encodings(self):
        text = open(self.test_file, 'rb').read().decode('utf8').encode(
            'ascii', 'xmlcharrefreplace'
        )
        doc1u = tidy.parseString(text, input_encoding='ascii',
                                 output_encoding='latin1')
        self.assertTrue(doc1u.getvalue().find(b'\xe9') >= 0)
        doc2u = tidy.parseString(text, input_encoding='ascii',
                                 output_encoding='utf8')
        self.assertTrue(doc2u.getvalue().find(b'\xc3\xa9') >= 0)

    def test_error_lines(self):
        for doc in self.default_docs():
            self.assertEquals(doc.errors[0].line, 1)

    def test_nonexisting(self):
        doc = tidy.parse(os.path.join(DATA_STORAGE, 'missing.html'))
        self.assertEquals(str(doc).strip(), '')
        self.assertIn('missing.html', doc.errors[0].message)
        if doc.errors[0].severity == 'E':
            self.assertEquals(doc.errors[0].severity, 'E')
            self.assertTrue(str(doc.errors[0]).startswith('Error'))
        else:
            # Tidy 5.5.19 and newer
            self.assertEquals(doc.errors[0].severity, 'D')
            self.assertTrue(str(doc.errors[0]).startswith('Document'))

    def test_options(self):
        doc1 = tidy.parseString(
            self.input1,
            add_xml_decl=1, show_errors=1, newline='CR', output_xhtml=1,
        )
        self.assertIn('CDATA', str(doc1))
        doc2 = tidy.parseString(
            "<Html>",
            add_xml_decl=1, show_errors=1, newline='CR', output_xhtml=1,
        )
        self.assertTrue(str(doc2).startswith('<?xml'))
        self.assertFalse(len(doc2.errors) == 0)
        self.assertNotIn('\n', str(doc2))
        doc3 = tidy.parse(self.test_file, char_encoding='utf8',
                          alt_text='foo')
        self.assertIn('alt="foo"', doc3.gettext())
        self.assertIn('é', doc3.gettext())

    def test_parse(self):
        doc1, doc2, doc3 = self.default_docs()
        self.assertIn('</html>', str(doc1))
        self.assertIn('</html>', str(doc2))
        self.assertIn('</html>', doc3.gettext())

    def test_big(self):
        text = 'x' * 16384
        doc = tidy.parseString('<html><body>{0}</body></html>'.format(text))
        self.assertIn(text, str(doc))

    def test_unicode(self):
        doc = tidy.parseString('<html><body>zkouška</body></html>')
        self.assertIn('zkouška', doc.gettext())

    def test_write(self):
        doc = tidy.parseString(self.input1)
        handle = six.BytesIO()
        doc.write(handle)
        self.assertEquals(str(doc), handle.getvalue())

    def test_errors(self):
        doc = tidy.parseString(self.input1)
        for error in doc.errors:
            self.assertTrue(str(error).startswith('line'))
            self.assertTrue(repr(error).startswith('ReportItem'))

    def test_report_item(self):
        item = tidy.ReportItem('Invalid: error')
        self.assertEqual(item.get_severity(), 'Invalid')

    def test_missing_load(self):
        backup = tidy.lib.LIBNAMES
        try:
            tidy.lib.LIBNAMES = ('not-existing-library',)
            with self.assertRaises(OSError):
                tidy.lib.Loader()
        finally:
            tidy.lib.LIBNAMES = backup
