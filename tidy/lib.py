from __future__ import annotations

import ctypes
import io
import os
import os.path
import weakref
from abc import ABC, abstractmethod
from errno import ENOMEM
from typing import (
    Any,
    BinaryIO,
    Callable,
    ClassVar,
    Mapping,
    TypeVar,
)

from tidy.error import InvalidOptionError, OptionArgError

LIBNAMES = (
    # Linux
    "libtidy.so",
    # MacOS
    "libtidy.dylib",
    # Windows
    "tidy",
    # Cygwin
    "cygtidy-0-99-0",
    # Linux, full soname
    "libtidy-0.99.so.0",
    # Linux, full soname
    "libtidy-0.99.so.0.0.0",
    # HTML tidy
    "libtidy.so.5",
    # Linux, HTML tidy v5.8
    "libtidy.so.58",
    # Debian changed soname
    "libtidy.so.5deb1",
    # Windows?
    "libtidy",
    # Windows?
    "tidylib",
)


class Loader:
    """
    ctypes.CDLL wrapper.

    I am a trivial wrapper that eliminates the need for tidy.tidyFoo,
    so you can just access tidy.Foo.
    """

    def __init__(self, libnames: tuple[str, ...] | None = None) -> None:
        self.lib: ctypes.CDLL
        self.libnames: tuple[str, ...] = libnames or LIBNAMES

        # Add package directory to search path
        os.environ["PATH"] = "".join(
            (os.path.dirname(__file__), os.pathsep, os.environ["PATH"]),
        )

        # Add full path to a library
        lib_path = os.environ.get("TIDY_LIBRARY_FULL_PATH")
        if lib_path:
            self.libnames = (lib_path, *self.libnames)

        # Try loading library
        for libname in self.libnames:
            try:
                self.lib = ctypes.CDLL(libname)
                break
            except OSError:
                continue
        else:
            # Fail in case we could not load it
            raise OSError("Couldn't find libtidy, please make sure it is installed.")

        # Adjust some types
        self.Create.restype = ctypes.POINTER(ctypes.c_void_p)
        self.LibraryVersion.restype = ctypes.c_char_p

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        return getattr(self.lib, "tidy%s" % name)


_tidy = Loader()


_putByteFunction = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_char)


# define a callback to pass to Tidylib
@_putByteFunction
def putByte(handle: int, char: int) -> int:
    """Lookup sink by handle and call its putByte method."""
    sinkfactory[handle].putByte(char)
    return 0


class _OutputSink(ctypes.Structure):
    _fields_ = (("sinkData", ctypes.c_int), ("putByte", _putByteFunction))


class _Sink:
    def __init__(self, handle: int) -> None:
        self._data = io.BytesIO()
        self.struct = _OutputSink()
        self.struct.putByte = putByte
        self.handle = handle

    def putByte(self, byte: bytes) -> None:
        self._data.write(byte)

    def getvalue(self) -> bytes:
        return self._data.getvalue()


class ReportItem:
    """Error report item as returned by tidy."""

    severities: ClassVar[dict[str, str]] = {
        "W": "Warning",
        "E": "Error",
        "C": "Config",
        "D": "Document",
    }

    def __init__(self, err: str) -> None:
        self.err: str = err  #: Whole error message as returned by tidy
        self.full_severity: str  #: Full severity string
        self.severity: str  #: D, W, E or C indicating severity
        self.message: str  #: Error message itself
        self.line: int | None  #: Line where error was fired (can be None)
        self.col: int | None  #: Column where error was fired (can be None)
        # Parses:
        # line <line number> column <column number> - (Error|Warning): <message>
        # It might be also useful to  gnu-emacs reporting mode
        if err.startswith("line"):
            tokens = err.split(" ", 6)
            self.full_severity = tokens[5]
            self.severity = tokens[5][0]  # W, E or C
            self.line = int(tokens[1])
            self.col = int(tokens[3])
            self.message = tokens[6]
        else:
            tokens = err.split(" ", 1)
            self.full_severity = tokens[0]
            self.severity = tokens[0][0]
            self.message = tokens[1]
            self.line = None
            self.col = None

    def get_severity(self) -> str:
        try:
            return self.severities[self.severity]
        except KeyError:
            return self.full_severity.strip().rstrip(":")

    def __str__(self) -> str:
        if self.line:
            return "line {} col {} - {}: {}".format(
                self.line,
                self.col,
                self.get_severity(),
                self.message,
            )
        return f"{self.get_severity()}: {self.message}"

    def __repr__(self) -> str:
        return "{}('{}')".format(self.__class__.__name__, str(self).replace("'", "\\'"))


K = TypeVar("K")
V = TypeVar("V")


class FactoryDict(ABC, dict, Mapping[K, V]):
    """
    Custom dict wrapper.

    I am a dict with a create method and no __setitem__.  This allows
    me to control my own keys.
    """

    @abstractmethod
    def create(self) -> V:
        """Generate a new item."""
        raise NotImplementedError

    def _setitem(self, name: K, value: V) -> None:
        dict.__setitem__(self, name, value)

    def __setitem__(self, _: K, __: V) -> None:
        raise TypeError("Use create() to get a new object")


class SinkFactory(FactoryDict[int, _Sink]):
    """Mapping for lookup of sinks by handle."""

    def __init__(self) -> None:
        super().__init__()
        self.lastsink: int = 0

    def create(self) -> _Sink:
        sink = _Sink(self.lastsink)
        sink.struct.sinkData = self.lastsink
        FactoryDict._setitem(self, self.lastsink, sink)  # noqa: SLF001
        self.lastsink = self.lastsink + 1
        return sink


sinkfactory = SinkFactory()

OPTION_TYPE = str | int | bool | None
OPTION_DICT_TYPE = dict[str, OPTION_TYPE]


class Document:
    """Document object as returned by :func:`parseString` or :func:`parse`."""

    def __init__(self, options: OPTION_DICT_TYPE) -> None:
        self.cdoc = _tidy.Create()
        self.options = options
        self.errsink = sinkfactory.create()
        _tidy.SetErrorSink(self.cdoc, ctypes.byref(self.errsink.struct))
        self._set_options()

    def _set_options(self) -> None:
        for key, value in self.options.items():
            # this will flush out most argument type errors...
            if value is None:
                value = ""  # noqa: PLW2901
            if isinstance(value, bool):
                value = int(value)  # noqa: PLW2901

            _tidy.OptParseValue(
                self.cdoc,
                key.replace("_", "-").encode("utf-8"),
                str(value).encode("utf-8"),
            )
            if self.errors:
                for error in ERROR_MAP:
                    if self.errors[-1].message.startswith(error):
                        raise ERROR_MAP[error](self.errors[-1].message)

    def __del__(self) -> None:
        del sinkfactory[self.errsink.handle]

    def write(self, stream: BinaryIO) -> None:
        """
        :param stream: Writable file like object.

        Writes document to the stream.
        """
        stream.write(self.getvalue())

    def get_errors(self) -> list[ReportItem]:
        """Return list of errors as a list of :class:`ReportItem`."""
        ret = []
        for line in self.errsink.getvalue().decode("utf-8").splitlines():
            line = line.strip()  # noqa: PLW2901
            if line:
                ret.append(ReportItem(line))
        return ret

    @property
    def errors(self) -> list[ReportItem]:
        return self.get_errors()

    def getvalue(self) -> bytes:
        """Raw string as returned by tidy."""
        stlen = ctypes.c_int(8192)
        string_buffer = ctypes.create_string_buffer(stlen.value)
        result = _tidy.SaveString(self.cdoc, string_buffer, ctypes.byref(stlen))
        if result == -ENOMEM:  # buffer too small
            string_buffer = ctypes.create_string_buffer(stlen.value)
            _tidy.SaveString(self.cdoc, string_buffer, ctypes.byref(stlen))
        return string_buffer.value

    def gettext(self) -> str:
        """Unicode text for output returned by tidy."""
        output_encoding = self.options["output_encoding"]
        assert isinstance(output_encoding, str)
        return self.getvalue().decode(output_encoding)

    def __str__(self) -> str:
        return self.gettext()


ERROR_MAP = {
    "missing or malformed argument for option: ": OptionArgError,
    "unknown option: ": InvalidOptionError,
}


class DocumentFactory(FactoryDict[weakref.ReferenceType, Document]):
    @staticmethod
    def load(
        doc: Document,
        arg: bytes,
        loader: Callable[[Document, bytes], int],
    ) -> None:
        status = loader(doc.cdoc, arg)
        if status >= 0:
            _tidy.CleanAndRepair(doc.cdoc)

    def loadFile(self, doc: Document, filename: str) -> None:
        self.load(doc, filename.encode("utf-8"), _tidy.ParseFile)

    def loadString(self, doc: Document, text: bytes) -> None:
        self.load(doc, text, _tidy.ParseString)

    def create(self, **kwargs: OPTION_TYPE) -> Document:
        enc = kwargs.get("char_encoding", "utf8")
        if "output_encoding" not in kwargs:
            kwargs["output_encoding"] = enc
        if "input_encoding" not in kwargs:
            kwargs["input_encoding"] = enc
        doc = Document(kwargs)
        ref = weakref.ref(doc, self.releaseDoc)
        FactoryDict._setitem(self, ref, doc.cdoc)  # noqa: SLF001
        return doc

    def parse(self, filename: str, **kwargs: OPTION_TYPE) -> Document:
        """
        Open and process filename as an HTML file.

        Returning a processed document object.

        :param kwargs: named options to pass to TidyLib for processing the
                       input file.
        :param filename: the name of a file to process
        :return: a :class:`Document` object

        """
        doc = self.create(**kwargs)
        self.loadFile(doc, filename)
        return doc

    def parseString(self, text: bytes | str, **kwargs: OPTION_TYPE) -> Document:
        """
        Use text as an HTML file.

        Returning a processed document object.

        :param kwargs: named options to pass to TidyLib for processing the
                       input file.
        :param text: the string to parse
        :return: a :class:`Document` object

        """
        doc = self.create(**kwargs)
        if isinstance(text, str):
            input_encoding = doc.options["input_encoding"]
            assert isinstance(input_encoding, str)
            text = text.encode(input_encoding)
        self.loadString(doc, text)
        return doc

    def releaseDoc(self, ref: weakref.ReferenceType) -> None:
        _tidy.Release(self[ref])


docfactory = DocumentFactory()
parse = docfactory.parse
parseString = docfactory.parseString


def getTidyVersion() -> str:
    version = _tidy.lib.tidyLibraryVersion()
    assert isinstance(version, bytes)
    return version.decode()
