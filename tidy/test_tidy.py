import io
import os
import pathlib
import unittest

import tidy
import tidy.lib

DATA_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")


class TidyTestCase(unittest.TestCase):
    input1 = "<html><script>1>2</script>"
    input2 = "<html>\n" + "<p>asdkfjhasldkfjhsldjas\n" * 100
    test_file = os.path.join(DATA_STORAGE, "test.html")

    def default_docs(self):
        doc1 = tidy.parseString(self.input1)
        doc2 = tidy.parseString(self.input2)
        doc3 = tidy.parse(self.test_file, char_encoding="ascii")
        return (doc1, doc2, doc3)

    def test_bad_options(self):
        badopts = [{"foo": 1}]
        for opts in badopts:
            with self.assertRaisesRegex(
                tidy.InvalidOptionError,
                "not a valid Tidy option",
            ):
                tidy.parseString(self.input2, **opts)

    def test_bad_option_values(self):
        badopts = [{"indent": "---"}, {"indent_spaces": None}]
        for opts in badopts:
            with self.assertRaisesRegex(
                tidy.OptionArgError,
                "missing or malformed argument",
            ):
                tidy.parseString(self.input2, **opts)

    def test_encodings(self):
        text = (
            pathlib.Path(self.test_file)
            .read_bytes()
            .decode("utf8")
            .encode("ascii", "xmlcharrefreplace")
        )
        doc1u = tidy.parseString(text, input_encoding="ascii", output_encoding="latin1")
        self.assertTrue(doc1u.getvalue().find(b"\xe9") >= 0)
        doc2u = tidy.parseString(text, input_encoding="ascii", output_encoding="utf8")
        self.assertTrue(doc2u.getvalue().find(b"\xc3\xa9") >= 0)

    def test_error_lines(self):
        for doc in self.default_docs():
            self.assertEqual(doc.errors[0].line, 1)

    def test_nonexisting(self):
        os.environ.pop("IGNORE_MISSING_TIDY", None)
        doc = tidy.parse(os.path.join(DATA_STORAGE, "missing.html"))
        self.assertEqual(str(doc).strip(), "")
        self.assertIn("missing.html", doc.errors[0].message)
        if doc.errors[0].severity == "E":
            self.assertEqual(doc.errors[0].severity, "E")
            self.assertTrue(str(doc.errors[0]).startswith("Error"))
        else:
            # Tidy 5.5.19 and newer
            self.assertEqual(doc.errors[0].severity, "D")
            self.assertTrue(str(doc.errors[0]).startswith("Document"))

    def test_options(self):
        doc1 = tidy.parseString(
            self.input1,
            add_xml_decl=1,
            show_errors=1,
            newline="CR",
            output_xhtml=True,
        )
        self.assertIn("CDATA", str(doc1))
        doc2 = tidy.parseString(
            "<Html>",
            add_xml_decl=1,
            show_errors=1,
            newline="CR",
            output_xhtml=True,
        )
        self.assertTrue(str(doc2).startswith("<?xml"))
        self.assertFalse(len(doc2.errors) == 0)
        self.assertNotIn("\n", str(doc2))
        doc3 = tidy.parse(self.test_file, char_encoding="utf8", alt_text="foo")
        self.assertIn('alt="foo"', doc3.gettext())
        self.assertIn("é", doc3.gettext())

    def test_parse(self):
        doc1, doc2, doc3 = self.default_docs()
        self.assertIn("</html>", str(doc1))
        self.assertIn("</html>", str(doc2))
        self.assertIn("</html>", doc3.gettext())

    def test_big(self):
        text = "x" * 16384
        doc = tidy.parseString(f"<html><body>{text}</body></html>")
        self.assertIn(text, str(doc))

    def test_unicode(self):
        doc = tidy.parseString("<html><body>zkouška</body></html>")
        self.assertIn("zkouška", doc.gettext())

    def test_write(self):
        doc = tidy.parseString(self.input1)
        handle = io.BytesIO()
        doc.write(handle)
        self.assertEqual(doc.getvalue(), handle.getvalue())

    def test_errors(self):
        doc = tidy.parseString(self.input1)
        for error in doc.errors:
            self.assertTrue(str(error).startswith("line"))
            self.assertTrue(repr(error).startswith("ReportItem"))

    def test_report_item(self):
        item = tidy.ReportItem("Invalid: error")
        self.assertEqual(item.get_severity(), "Invalid")

    def test_missing_load(self):
        with self.assertRaises(OSError):
            tidy.lib.Loader(libnames=("not-existing-library",))

    def test_lib_from_environ(self):
        os.environ["TIDY_LIBRARY_FULL_PATH"] = "/foo/bar/tidy"
        loader = tidy.lib.Loader()
        expected_libnames = (
            "/foo/bar/tidy",
            "libtidy.so",
            "libtidy.dylib",
            "tidy",
            "cygtidy-0-99-0",
            "libtidy-0.99.so.0",
            "libtidy-0.99.so.0.0.0",
            "libtidy.so.5",
            "libtidy.so.58",
            "libtidy.so.5deb1",
            "libtidy",
            "tidylib",
        )
        self.assertEqual(loader.libnames, expected_libnames)

    def test_lib_version(self):
        self.assertEqual(len(tidy.lib.getTidyVersion().split(".")), 3)


if __name__ == "__main__":
    unittest.main()
