# sectoolkit
Tools for working with Securities and Exchange Commission (SEC) indices, SGML header files, filing archives and individual filing documents.

This package supports working with SEC indexes, SGML header files and filings, including individual or bulk downloading and local caching of these items.  Package architecture supports form parsers as plug-in classes.

### Installation

The package can be installed via pip using the following statement:

`pip install sectoolkit`

Alternatively, package files can be  downloaded from the github repository located at https://github.com/dlouton/sectoolkit and installed manually.

### Working with SEC index files

The `idx` class provides an interface to the SEC's collection of quarterly index files.

**Required arguments:**

*user_agent* 	:    	(default = None)   The SEC requires that all files requests contain a header 
									specifying a user agent string of the form "company or institution name, 									contact email".  See the SEC developer page for further details: 
									https://www.sec.gov/os/accessing-edgar-data

**Optional arguments:**

*datadir*             :   	(default creates 'secdata' subdirectory under the current directory)  This is 
                        			where locally cached SEC files will be stored.
*start_year*          :   	(default = 1993 specifies the start of the SEC's online filing collection)
*start_quarter*	:   	(default = 1)
*end_year*           :  	 (default = 0, which specifies the current year)
*end_quarter*     :   	(default = 4)
*rate_limiter*       :   	(defaults to the rate_limiter class provided in limiter sub-package)
*binary_file_types*   :   (defaults to ['gz', 'zip', 'Z'])

**Methods:**

*clear_header_cache()*
		Delete locally cached SGML header files.

*clear_index_cache()*
		Delete locally cached SEC index files.

*fetch_filings(headers = False, verbose=False)*
		Fetch the filing archive files for filings included in the current working index if they are 
		not already present in the local file cache.  Optionally, specify the headers=True option 
		to fetch the related SGML header file if it is not already locally cached.

*fetch_headers(verbose=False)*
		Fetch the SGML header files for filings included in the current working index if they are not already 
		present in the local cache.

*filter_index(filters = {}, verbose = False)*
		Apply filters to the full set of index files for the date range specified in the index dictionary
        to create a working index, which is stored under the `working_idx` instance attribute as a 
		Pandas dataframe.  Filters are supplied in the form of a dictionary with column names as 
		keys.  Currently date range filtering is not directly supported, however, date range filters can 
		be applied directly to the `working_idx` dataframe within Pandas.

*index_peek(rows=5)*
		Read a specified number of rows from the index file for the most recent quarter in the 
		date range specified in the instance dictionary.

*show_index_fields()*
		Return index file column names and data types.

*updateidx()*
		Updates the locally cached quarterly index files for the date range specified in the instance 
		dictionary.  By default the most recent quarterly index file included in the local cache is deleted 
		and replaced by the most current version available from the SEC website.

**Example:**

```
import sectoolkit as sec

# Define a user-agent as per SEC developer guidelines.
user_agent_str = "<company or institution>, <contact email>"

# Instantiate the idx class
idx = sec.idx(start_year = 2020, datadir = '.\secdata', user_agent = user_agent_str)

# Specify filters as desired
filters = {'CIK': ['1336528'], 'Form Type': ['SC 13D']}

# Apply filters to populate idx.working_idx dataframe with filtered index records.
idx.filter_index(filters)

# If desired, bulk download all filings listed in idx.working_idx
# Optionally include the SGML header files by specifying headers = True
idx.fetch_filings(verbose=True)

# Alternatively, just download the SGML header files in order to access
# more detailed meta data on each filing.
idx.fetch_headers(verbose=True)
```

### Working with header files

< More to come here >

### Working with filing archives

< More to come here >

### Parsing filing text

Parsing of filings is currently only supported for forms SC 13D and SC 13D/A, however, support for forms 8-K and 8-K/A will be added shortly. 

Package architecture supports form parsers as plug-in classes that accept the file body and optional key word arguments as inputs and implement a _parsing_work_function(self) method that populates the self.parsed dictionary object with items that are of interest for a particular form type. Users can develop their own custom parsers and register them as the default for a particular form type. Alternatively, an instance of a custom parser can be registered under the self.parser attribute of an instance of the filingDocument class.  Calls to the self.parse() method of the filingDocument class will first check the self.parser instance attribute for a parser and will then check the parsers dictionary to see whether there is a default parser for the form type in question. 

#### Adding a custom parser
To implement a custom parser, sub-class the following parser base class, which is exposed in the package level namespace.
```
class parser_base(object):

    def __init__(self, file_body, **kwargs):
        # self.body = file_body
        # Add any optional key word arguments that were provided to 
        # the instance dictionary
        self.__dict__.update(kwargs)
        # Initialize the dictionary that will receive parsed items
        self.parsed = {}

    # Override this function in parser subclasses to implement parsers 
    # for specific form types.
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
You can then add your custom parser to the parsers dictionary as the default for particular form types.  For example, if you created an 8-K parser with class name parser_8K, you would add it as follows:
```
sectoolkit.parsers['8-K'] = parser_8K
sectoolkit.parsers['8-K/A'] = parser_8K
```
Also, note the support for optional keyword arguments when instantiating the parser class.  These items are added to the instance `__dict__` for the parser and are then available to be accessed by the parsing code included in the body of the parser class. 



