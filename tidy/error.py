"""
Exceptions for uTidylib
"""

__all__ = ("TidyLibError", "InvalidOptionError", "OptionArgError")


class TidyLibError(Exception):
    """
    Generic Tidy exception.
    """

    pass


class InvalidOptionError(TidyLibError):
    """
    Exception for invalid option.
    """

    def __str__(self) -> str:
        return "%s was not a valid Tidy option." % (self.args[0])


class OptionArgError(TidyLibError):
    """
    Exception for invalid parameter.
    """

    pass
