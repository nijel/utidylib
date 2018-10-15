import os.path
import os
import ctypes
import weakref

import six

from tidy.error import InvalidOptionError, OptionArgError

LIBNAMES = (
    # Linux
    'libtidy.so',
    # MacOS
    'libtidy.dylib',
    # Windows
    'tidy',
    # Cygwin
    'cygtidy-0-99-0',
    # Linux, full soname
    'libtidy-0.99.so.0',
    # Linux, full soname
    'libtidy-0.99.so.0.0.0',
    # HTML tidy
    'libtidy.so.5',
    # Windows?
    'libtidy',
    # Windows?
    'tidylib',
)


class Loader(object):
    """I am a trivial wrapper that eliminates the need for tidy.tidyFoo,
    so you can just access tidy.Foo
    """
    def __init__(self):
        self.lib = None

        # Add package directory to search path
        os.environ['PATH'] = ''.join(
            (os.path.dirname(__file__), os.pathsep, os.environ['PATH'])
        )

        # Try loading library
        for libname in LIBNAMES:
            try:
                self.lib = ctypes.CDLL(libname)
                break
            except OSError:
                continue

        # Fail in case we could not load it
        if self.lib is None and 'IGNORE_MISSING_TIDY' not in os.environ:
            raise OSError(
                "Couldn't find libtidy, please make sure it is installed."
            )

        # Adjust some types
        if self.lib is not None:
            self.Create.restype = ctypes.POINTER(ctypes.c_void_p)

    def __getattr__(self, name):
        return getattr(self.lib, "tidy%s" % name)


_tidy = Loader()


_putByteFunction = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_char)


# define a callback to pass to Tidylib
@_putByteFunction
def putByte(handle, char):
    """Lookup sink by handle and call its putByte method"""
    sinkfactory[handle].putByte(char)
    return 0


class _OutputSink(ctypes.Structure):
    _fields_ = [
        ("sinkData", ctypes.c_int),
        ("putByte", _putByteFunction),
    ]


class _Sink(object):
    def __init__(self, handle):
        self._data = six.BytesIO()
        self.struct = _OutputSink()
        self.struct.putByte = putByte
        self.handle = handle

    def putByte(self, byte):
        self._data.write(byte)

    def getvalue(self):
        return self._data.getvalue()


class ReportItem(object):
    """
    Error report item as returned by tidy.

    :attribute severity: D, W, E or C indicating severity
    :attribute line: Line where error was fired (can be None)
    :attribute col: Column where error was fired (can be None)
    :attribute message: Error message itsef
    :attribute err: Whole error message as returned by tidy
    """
    severities = {
        'W': 'Warning',
        'E': 'Error',
        'C': 'Config',
        'D': 'Document',
    }

    def __init__(self, err):
        # TODO - parse emacs mode
        self.err = err
        if err.startswith('line'):
            tokens = err.split(' ', 6)
            self.full_severity = tokens[5]
            self.severity = tokens[5][0]  # W, E or C
            self.line = int(tokens[1])
            self.col = int(tokens[3])
            self.message = tokens[6]
        else:
            tokens = err.split(' ', 1)
            self.full_severity = tokens[0]
            self.severity = tokens[0][0]
            self.message = tokens[1]
            self.line = None
            self.col = None

    def get_severity(self):
        try:
            return self.severities[self.severity]
        except KeyError:
            return self.full_severity.strip().rstrip(':')

    def __str__(self):
        if self.line:
            return "line {0} col {1} - {2}: {3}".format(
                self.line,
                self.col,
                self.get_severity(),
                self.message
            )

        else:
            return "{0}: {1}".format(
                self.get_severity(),
                self.message
            )

    def __repr__(self):
        return "{0}('{1}')".format(
            self.__class__.__name__,
            str(self).replace("'", "\\'")
        )


class FactoryDict(dict):
    """I am a dict with a create method and no __setitem__.  This allows
    me to control my own keys.
    """
    def create(self):
        """Subclasses should implement me to generate a new item"""

    def _setitem(self, name, value):
        dict.__setitem__(self, name, value)

    def __setitem__(self, name, value):
        raise TypeError("Use create() to get a new object")


class SinkFactory(FactoryDict):
    """Mapping for lookup of sinks by handle"""
    def __init__(self):
        FactoryDict.__init__(self)
        self.lastsink = 0

    def create(self):
        sink = _Sink(self.lastsink)
        sink.struct.sinkData = self.lastsink
        FactoryDict._setitem(self, self.lastsink, sink)
        self.lastsink = self.lastsink + 1
        return sink


sinkfactory = SinkFactory()


class Document(object):
    """
    Document object as returned by :func:`parseString` or :func:`parse`.
    """
    def __init__(self, options):
        self.cdoc = _tidy.Create()
        self.options = options
        self.errsink = sinkfactory.create()
        _tidy.SetErrorSink(self.cdoc, ctypes.byref(self.errsink.struct))

    def __del__(self):
        del sinkfactory[self.errsink.handle]

    def write(self, stream):
        '''
        :param stream: Writable file like object.

        Writes document to the stream.
        '''
        stream.write(self.getvalue())

    def get_errors(self):
        '''
        Returns list of errors as a list of :class:`ReportItem`.
        '''
        ret = []
        for line in self.errsink.getvalue().decode('utf-8').splitlines():
            line = line.strip()
            if line:
                ret.append(ReportItem(line))
        return ret

    errors = property(get_errors)

    def getvalue(self):
        """Raw string as returned by tidy."""
        stlen = ctypes.c_int(8192)
        string_buffer = ctypes.c_buffer(stlen.value)
        result = _tidy.SaveString(
            self.cdoc, string_buffer, ctypes.byref(stlen)
        )
        if result == -12:  # buffer too small
            string_buffer = ctypes.c_buffer(stlen.value)
            _tidy.SaveString(self.cdoc, string_buffer, ctypes.byref(stlen))
        return string_buffer.value

    def gettext(self):
        """Unicode text for output returned by tidy."""
        return self.getvalue().decode(self.options['output_encoding'])

    def __str__(self):
        if six.PY3:
            return self.gettext()
        return self.getvalue()


ERROR_MAP = {
    'missing or malformed argument for option: ': OptionArgError,
    'unknown option: ': InvalidOptionError,
}


class DocumentFactory(FactoryDict):
    def _setOptions(self, doc, **options):
        for k in options.keys():

            # this will flush out most argument type errors...
            if options[k] is None:
                options[k] = ''

            _tidy.OptParseValue(doc.cdoc,
                                k.replace('_', '-'),
                                str(options[k]))
            if doc.errors:
                for error in ERROR_MAP:
                    if doc.errors[-1].message.startswith(error):
                        raise ERROR_MAP[error](doc.errors[-1].message)

    def load(self, doc, arg, loader):
        status = loader(doc.cdoc, six.binary_type(arg))
        if status > 0:
            _tidy.CleanAndRepair(doc.cdoc)

    def loadFile(self, doc, filename):
        self.load(doc, filename, _tidy.ParseFile)

    def loadString(self, doc, text):
        self.load(doc, text, _tidy.ParseString)

    def _create(self, **kwargs):
        enc = kwargs.get('char-encoding', 'utf8')
        if 'output_encoding' not in kwargs:
            kwargs['output_encoding'] = enc
        if 'input_encoding' not in kwargs:
            kwargs['input_encoding'] = enc
        doc = Document(kwargs)
        self._setOptions(doc, **kwargs)
        ref = weakref.ref(doc, self.releaseDoc)
        FactoryDict._setitem(self, ref, doc.cdoc)
        return doc

    def parse(self, filename, **kwargs):
        """
        :param kwargs: named options to pass to TidyLib for processing the
                       input file.
        :param filename: the name of a file to process
        :return: a :class:`Document` object

        Open and process filename as an HTML file, returning a
        processed document object.
        """
        doc = self._create(**kwargs)
        self.loadFile(doc, filename)
        return doc

    def parseString(self, text, **kwargs):
        """
        :param kwargs: named options to pass to TidyLib for processing the
                       input file.
        :param text: the string to parse
        :return: a :class:`Document` object

        Use text as an HTML file, and process it, returning a
        document object.
        """
        doc = self._create(**kwargs)
        if isinstance(text, six.text_type):
            text = text.encode(doc.options['input_encoding'])
        self.loadString(doc, text)
        return doc

    def releaseDoc(self, ref):
        _tidy.Release(self[ref])


docfactory = DocumentFactory()
parse = docfactory.parse
parseString = docfactory.parseString
