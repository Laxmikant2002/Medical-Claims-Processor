class ProcessingError(Exception):
    """Raised when document processing fails."""
    pass

class ValidationError(Exception):
    """Raised when document validation fails."""
    pass

class ExtractionError(Exception):
    """Raised when data extraction fails."""
    pass

class ClassificationError(Exception):
    """Raised when document classification fails."""
    pass

class ConfigurationError(Exception):
    """Raised when there are configuration issues."""
    pass

class FileError(Exception):
    """Raised when there are issues with file handling."""
    pass 