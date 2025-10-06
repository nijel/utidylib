"""Exceptions for uTidylib."""

from __future__ import annotations

__all__ = ("InvalidOptionError", "OptionArgError", "TidyLibError")


class TidyLibError(Exception):
    """Generic Tidy exception."""


class InvalidOptionError(TidyLibError):
    """Exception for invalid option."""

    def __str__(self) -> str:
        return f"{self.args[0]} was not a valid Tidy option."


class OptionArgError(TidyLibError):
    """Exception for invalid parameter."""
