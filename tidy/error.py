__all__ = ('TidyLibError', 'InvalidOptionError', 'OptionArgError',
           )
           
class TidyLibError(Exception):
    def __init__(self, arg):
        self.arg=arg

class InvalidOptionError(TidyLibError):
    def __str__(self):
        return "%s was not a valid Tidy option." % (self.arg)
    __repr__=__str__

class OptionArgError(TidyLibError):
    def __init__(self, arg):
        self.arg=arg
    def __str__(self):
        return self.arg