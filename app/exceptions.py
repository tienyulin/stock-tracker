"""
Custom exceptions for Stock Tracking System.
"""


class StockTrackerError(Exception):
    """Base exception for Stock Tracker."""
    pass


class ValidationError(StockTrackerError):
    """Validation error."""
    pass


class SymbolNotFoundError(StockTrackerError):
    """Symbol not found error."""
    pass


class NetworkError(StockTrackerError):
    """Network related error."""
    pass


class RateLimitError(StockTrackerError):
    """Rate limit exceeded error."""
    pass


class DataSourceError(StockTrackerError):
    """Data source error."""
    pass


class CacheError(StockTrackerError):
    """Cache related error."""
    pass
