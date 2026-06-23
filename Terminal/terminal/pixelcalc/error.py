class CalcError(Exception):
    """Base error for pixelcalc."""


class CellError(CalcError):
    """Base error for cell logic."""


class InvalidCellDataError(CellError):
    """Cell pixel data is invalid."""


class ExtractorError(CalcError):
    """Base error for extractor logic."""


class ExtractorDecodeError(ExtractorError):
    """Extractor decode flow failed."""


class TitleError(CalcError):
    """Base error for title manager logic."""


class TitleValidationError(TitleError):
    """Title input data is invalid."""


class TitleHashMismatchError(TitleError):
    """The supplied hash does not match valid_array."""


class TitleRecordNotFoundError(TitleError):
    """The requested title record does not exist."""


class TitleImportError(TitleError):
    """Importing title data failed."""
