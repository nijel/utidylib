import os.path
import os
import ctypes
import six
import weakref
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
        try:
            return getattr(self.lib, "tidy%s" % name)
        # current ctypes uses ValueError, future will use AttributeError
        except (ValueError, AttributeError):
            return getattr(self.lib, name)


_tidy = Loader()


# define a callback to pass to Tidylib
def _putByte(handle, char):
    """Lookup sink by handle and call its putByte method"""
    sinkfactory[handle].putByte(char)
    return 0


PUTBYTEFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_char)
putByte = PUTBYTEFUNC(_putByte)


class _OutputSink(ctypes.Structure):
    _fields_ = [
        ("sinkData", ctypes.c_int),
        ("putByte", PUTBYTEFUNC),
    ]


class _Sink(object):
    def __init__(self):
        self._data = six.BytesIO()
        self.struct = _OutputSink()
        self.struct.putByte = putByte

    def putByte(self, byte):
        self._data.write(bute)

    def __str__(self):
        return self._data.getvalue()


class ReportItem(object):
    severities = {'W': 'Warning', 'E': 'Error', 'C': 'Config'}

    def __init__(self, err):
        # TODO - parse emacs mode
        self.err = err
        if err.startswith('line'):
            tokens = err.split(' ', 6)
            self.severity = tokens[5][0]  # W or E
            self.line = int(tokens[1])
            self.col = int(tokens[3])
            self.message = tokens[6]
        else:
            tokens = err.split(' ', 1)
            self.severity = tokens[0][0]
            self.message = tokens[1]
            self.line = None
            self.col = None

    def __str__(self):
        try:
            if self.line:
                return "line %d col %d - %s: %s" % (self.line, self.col,
                                                    severities[self.severity],
                                                    self.message)

            else:
                return "%s: %s" % (self.severities[self.severity], self.message)
        except KeyError:
            return self.err

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__,
                             str(self).replace("'", "\\'"))


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
        sink = _Sink()
        sink.struct.sinkData = self.lastsink
        FactoryDict._setitem(self, self.lastsink, sink)
        self.lastsink = self.lastsink + 1
        return sink


sinkfactory = SinkFactory()


class _Document(object):
    def __init__(self):
        self.cdoc = _tidy.Create()
        self.errsink = sinkfactory.create()
        _tidy.SetErrorSink(self.cdoc, ctypes.byref(self.errsink.struct))

    def write(self, stream):
        stream.write(str(self))

    def get_errors(self):
        ret = []
        for line in str(self.errsink).split('\n'):
            line = line.strip(' \n\r')
            if line:
                ret.append(ReportItem(line))
        return ret

    errors = property(get_errors)

    def __str__(self):
        stlen = ctypes.c_int(8192)
        st = ctypes.c_buffer(stlen.value)
        rc = _tidy.SaveString(self.cdoc, st, ctypes.byref(stlen))
        if rc == -12:  # buffer too small
            st = ctypes.c_buffer(stlen.value)
            _tidy.SaveString(self.cdoc, st, ctypes.byref(stlen))
        return st.value

errors = {
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
                match = list(filter(
                    doc.errors[-1].message.startswith,
                    errors.keys()
                ))
                if match:
                    raise errors[match[0]](doc.errors[-1].message)

    def load(self, doc, arg, loader):
        loader(doc.cdoc, six.binary_type(arg))
        _tidy.CleanAndRepair(doc.cdoc)

    def loadFile(self, doc, filename):
        self.load(doc, filename, _tidy.ParseFile)

    def loadString(self, doc, text):
        self.load(doc, text, _tidy.ParseString)

    def _create(self, **kwargs):
        doc = _Document()
        self._setOptions(doc, **kwargs)
        ref = weakref.ref(doc, self.releaseDoc)
        FactoryDict._setitem(self, ref, doc.cdoc)
        return doc

    def parse(self, filename, **kwargs):
        """
        :param kwargs: named options to pass to TidyLib for processing the
                       input file.
        :param filename: the name of a file to process
        :return: a document object

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
        :return: a document object

        Use text as an HTML file, and process it, returning a
        document object.
        """
        if type(text) == six.text_type:
            try:
                enc = kwargs['char_encoding']
            except KeyError:
                enc = 'utf8'
                kwargs['char_encoding'] = enc
            text = text.encode(enc)
        doc = self._create(**kwargs)
        self.loadString(doc, text)
        return doc

    def releaseDoc(self, ref):
        _tidy.Release(self[ref])


docfactory = DocumentFactory()
parse = docfactory.parse
parseString = docfactory.parseString
