"""User-facing errors raised by the CLI and SDK."""


class DictionarianError(RuntimeError):
    """Base error for expected product failures."""


class AuthenticationError(DictionarianError):
    """Raised when no valid customer token is available."""


class ConfigurationError(DictionarianError):
    """Raised when local project configuration is invalid."""


class InsufficientCreditsError(DictionarianError):
    """Raised when an account cannot fund a generation request."""

