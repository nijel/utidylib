from __future__ import generators

import sys
import os.path
packagedir = os.path.dirname(__file__)

# look for ctypes in the system path, then try looking for a private ctypes
# distribution
try:
    import ctypes
except ImportError:
    private_ctypes = os.path.join(packagedir, 'pvt_ctypes')
    sys.path.insert(0, private_ctypes)
    sys.path.insert(0, os.path.join(private_ctypes, 'ctypes.zip'))
    import ctypes
from cStringIO import StringIO
import weakref
from tidy.error import InvalidOptionError, OptionArgError

# search the path for libtidy using the known names; try the package
# directory too
thelib = None
os.environ['PATH'] = "%s%s%s" % (packagedir, os.pathsep, os.environ['PATH'])
for libname in ('tidy', 'cygtidy-0-99-0', 'libtidy', 'libtidy.so',
                'libtidy-0.99.so.0', 'tidylib', 'libtidy.dylib'):
    try:
        thelib = getattr(ctypes.cdll, libname)
        break
    except OSError:
        pass
if not thelib:
    raise OSError("Couldn't find libtidy, please make sure it is installed.")


class Loader(object):
    """I am a trivial wrapper that eliminates the need for tidy.tidyFoo,
    so you can just access tidy.Foo
    """
    def __init__(self):
        self.lib = thelib

    def __getattr__(self, name):
        try:
            return getattr(self.lib, "tidy%s" % name)
        # current ctypes uses ValueError, future will use AttributeError
        except (ValueError, AttributeError):
            return getattr(self.lib, name)


_tidy = Loader()
_tidy.Create.restype = ctypes.POINTER(ctypes.c_void_p)


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
        self._data = StringIO()
        self.struct = _OutputSink()
        self.struct.putByte = putByte

    def putByte(self, c):
        self._data.write(c)

    def __str__(self):
        return self._data.getvalue()


class ReportItem(object):
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
        severities = dict(W='Warning', E='Error', C='Config')
        try:
            if self.line:
                return "line %d col %d - %s: %s" % (self.line, self.col,
                                                    severities[self.severity],
                                                    self.message)

            else:
                return "%s: %s" % (severities[self.severity], self.message)
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
        self.lastsink = self.lastsink+1
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
                match = filter(
                    doc.errors[-1].message.startswith,
                    errors.keys()
                )
                if match:
                    raise errors[match[0]](doc.errors[-1].message)

    def load(self, doc, arg, loader):
        loader(doc.cdoc, arg)
        _tidy.CleanAndRepair(doc.cdoc)

    def loadFile(self, doc, filename):
        self.load(doc, filename, _tidy.ParseFile)

    def loadString(self, doc, st):
        self.load(doc, st, _tidy.ParseString)

    def _create(self, *args, **kwargs):
        doc = _Document()
        self._setOptions(doc, **kwargs)
        ref = weakref.ref(doc, self.releaseDoc)
        FactoryDict._setitem(self, ref, doc.cdoc)
        return doc

    def parse(self, filename, *args, **kwargs):
        """Open and process filename as an HTML file, returning a
        processed document object.
        @param kwargs: named options to pass to TidyLib for processing
        the input file.
        @param filename: the name of a file to process
        @return: a document object
        """
        doc = self._create(**kwargs)
        self.loadFile(doc, filename)
        return doc

    def parseString(self, st, *args, **kwargs):
        """Use st as an HTML file, and process it, returning a
        document object.
        @param kwargs: named options to pass to TidyLib for processing
        the input file.
        @param st: the string to parse
        @return: a document object
        """
        if type(st) == unicode:
            try:
                enc = kwargs['char_encoding']
            except KeyError:
                enc = 'utf8'
                kwargs['char_encoding'] = enc
            st = st.encode(enc)
        doc = self._create(**kwargs)
        self.loadString(doc, st)
        return doc

    def releaseDoc(self, ref):
        _tidy.Release(self[ref])


docfactory = DocumentFactory()
parse = docfactory.parse
parseString = docfactory.parseString
