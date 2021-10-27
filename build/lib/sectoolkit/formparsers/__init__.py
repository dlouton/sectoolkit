

from .parser_base import parser_base
from .parser_13D import parser_13D

# Register available parsers
parsers = {
	'SC 13D': parser_13D,
	'SC 13D/A': parser_13D
}