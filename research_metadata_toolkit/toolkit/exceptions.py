"""Custom exceptions raised by the Research Metadata Toolkit."""


class ToolkitError(Exception):
    """Base exception for toolkit errors."""


class ExcelFileError(ToolkitError):
    """Raised when an Excel workbook cannot be loaded or saved."""


class MissingColumnError(ToolkitError):
    """Raised when a required spreadsheet column is missing."""


class InvalidDOIError(ToolkitError):
    """Raised when a DOI value is invalid for a strict operation."""


class InvalidURLError(ToolkitError):
    """Raised when a URL value is invalid for a strict operation."""


class MetadataAPIError(ToolkitError):
    """Raised when a metadata API request fails unexpectedly."""
