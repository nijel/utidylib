"""
Exceptions for uTidyLib
"""

__all__ = (
    'TidyLibError', 'InvalidOptionError', 'OptionArgError',
)


class TidyLibError(Exception):
    """
    Generic Tidy exception.
    """
    def __init__(self, arg):
        self.arg = arg
        super(TidyLibError, self).__init__(arg)

    def __str__(self):
        return self.arg


class InvalidOptionError(TidyLibError):
    """
    Exception for invalid option.
    """
    def __str__(self):
        return "%s was not a valid Tidy option." % (self.arg)
    __repr__ = __str__


class OptionArgError(TidyLibError):
    """
    Exception for invalid parameter.
    """
    pass
