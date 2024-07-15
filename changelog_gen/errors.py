class ChangelogException(Exception):  # noqa: N818
    """Base exception class."""


class NoReleaseNotesError(ChangelogException):
    """No release notes directory found."""


class InvalidSectionError(ChangelogException):
    """Unsupported section detected."""


class VcsError(ChangelogException):
    """Version control error."""


class VersionError(ChangelogException):
    """Bumpversion error."""


class ParseError(ChangelogException):
    """Parse error."""


class SerialiseError(ChangelogException):
    """Serialise error."""


class BumpError(ChangelogException):
    """Version bump error."""


class UnsupportedReplaceError(ChangelogException):
    """Unsupported ::replace:: in configuration string."""


class UnsupportedParserError(ChangelogException):
    """Unsupported parser in configuration."""


class UnsupportedSerialiserError(ChangelogException):
    """Unsupported serialiser in configuration."""
