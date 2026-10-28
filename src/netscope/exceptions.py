class InvalidTargetError(ValueError):
    """Raised when the user enters invalid network target"""


class InvalidPortError(ValueError):
    """Raised when a TCP port or port range is invalid."""


class UnsupportedPlatformError(RuntimeError):
    """Raised when the operating system has no supported command."""
