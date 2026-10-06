class BGGError(Exception):
    """BoardGameGeek couldn't provide the data."""

class BGGAuthError(BGGError):
    """BoardGameGeek rejected the API key."""
