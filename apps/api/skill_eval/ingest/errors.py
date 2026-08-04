class ParseError(Exception):
    """Raised when an adapter cannot parse raw agent data into a canonical Trace."""


class ParseWarning(UserWarning):
    """Non-fatal parse issues worth surfacing (e.g. unknown events ignored)."""
