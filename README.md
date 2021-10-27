# sectoolkit
Tools for working with Securities and Exchange Commission (SEC) indices, SGML header files, filing archives and individual filing documents.

This package supports working with SEC indexes, SGML header files and filings, including individual or bulk downloading and local caching of these items.

Package architecture supports form parsers as plug-in classes that accept the file body and optional key word arguments as inputs and implement a _parsing_work_function(self) method that populates the self.parsed dictionary object with items that are of interest for a particular form type. Users can develop their own custom parsers and register them as the default for a particular form type. Alternatively, an instance of a custom parser can be registered under the self.parser attribute of an instance of the filingDocument class.  Calls to the self.parse() method of the filingDocument class will first check the self.parser instance attribute for a parser and will then check the parsers dictionary to see whether there is a default parser for the form type in question.  
 
## Parsing filing text
Parsing of filings is currently only supported for forms SC 13D and SC 13D/A, however, support for forms 8-K and 8-K/A will be added shortly. 

### Adding a custom parser
To implement a custom parser, sub-class the following parser base class, which is exposed in the package level namespace.
```
class parser_base(object):

    def __init__(self, file_body, **kwargs):
        # 
        self.body = file_body
        # Include any optional key word arguments that were provided in 
        # the instance dictionary
        self.__dict__.update(kwargs)
        # Initialize the dictionary that will receive parsed items
        self.parsed = {}

    # Override this in parser subclasses to implement parsers for different form types.
    def _parsing_work_function(self):
        # Get all the real work done here and in other internal functions

        # For example, set a test entry in the self.parsed dictionary
        # self.parsed['test'] = 'pass'
        pass

    def parse(self):
        # Call one or more internal functions that will populate the 
        # self.parsed dictionary
        self._parsing_work_function()
  
        # Return the dictionary of parsed items.
        return self.parsed
```
You can then add it to the parsers dictionary as the default for particular form types as follows:
```
`sectoolkit.parsers['8-K'] = parser_8K`
`sectoolkit.parsers['8-K/A'] = parser_8K`
```
Also, note the support for optional keyword arguments when instantiating the parser class.  These items are added to the instance `__dict__` for the parser and are then available to be accessed by the parsing code included in the body of the parser class. 



