# sectoolkit
Tools for working with Securities and Exchange Commission (SEC) indices, SGML header files, filing archives and individual filing documents.

This package supports working with SEC indexes, SGML header files and filings, including individual or bulk downloading and local caching of these items.

Package architecture supports form parsers as plug-in classes that accept the file body and optional key word arguments as inputs and implement a parse() method that returns a dictionary object containing parsed items. Users can develop their own custom parsers and register them as the default for a particular filing type.

 
## Parsing filing text
Parsing of filings is currently only supported for forms SC 13D and SC 13D/A, however, support for forms 8-K and 8-K/A will be added shortly. 

### Adding a custom parser
To implement a custom parser, use the following stub class as a starting point:
```
# The parser classes are generally named parser_<form_type>
class parser_8K(object):

    def __init__(self, file_body, **kwargs):
        # 
        self.body = file_body
        # Include any optional key word arguments that were provided in the instance dictionary
        self.__dict__.update(kwargs)
        # Initialize the dictionary that will receive parsed items
        self.parsed = {}

    def _workhorse_function(self):
        # Get all the real work done here and in other internal functions
        pass

    def parse(self):
        # Call one or more internal functions that will populate the self.parsed dictionary
        self._workhorse_function()
  
        self.parsed['test'] = 'pass'
        # Return the dictionary of parsed items.
        return self.parsed
```
You can then add it to the parsers dictionary as the default for particular form types as follows:

`sectoolkit.parsers['8-K'] = parser_8K`
`sectoolkit.parsers['8-K/A'] = parser_8K`

Also, note the support for optional keyword arguments when instantiating the parser class.  These items are added to the instance `__dict__` for the parser and are then available to be accessed by the parsing code included in the body of the parser class. 



