__version__ = "0.2.4"

# Import items from sub-modules into sectoolkit namespace
from .secmeta import (idx, headerfile)
from .secfiling import (filingDocument, filingArchive)
from .formparsers import parsers, parser_base
from .limiter import rate_limiter
from .utils import get_ticker_name_dicts