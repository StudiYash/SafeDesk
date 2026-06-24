"""Custom exceptions for SafeDesk configuration handling."""


class SafeDeskConfigError(Exception):
    """Base class for SafeDesk configuration errors."""


class SafeDeskConfigFileError(SafeDeskConfigError):
    """Raised when a configuration file cannot be read or parsed."""


class SafeDeskEnvironmentError(SafeDeskConfigError):
    """Raised when environment values are invalid."""


class SafeDeskValidationError(SafeDeskConfigError):
    """Raised when configuration validation fails."""
