"""Exceptions raised by the Member 1 data foundation."""


class DataError(Exception):
    """Base class for expected data-pipeline errors."""


class MetadataValidationError(DataError):
    """A raster has missing or invalid geospatial metadata."""


class SpatialLeakageError(DataError):
    """Geographic split regions overlap or samples are ambiguously assigned."""


class DataContractError(DataError):
    """An artifact does not satisfy the downstream data contract."""
