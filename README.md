# sectoolkit
Tools for working with Securities and Exchange Commission (SEC) indices and filings.

This package supports working with SEC indexes, SGML header files and filings, including individual or bulk downloading and local caching of these items. Parsing of filings is currently only supported for forms SC 13D and SC 13D/A, however, support for parsing forms 8-K and 8-K/A will be added shortly. Package architecture supports form parsers as plug-in classes that accept the file body as input and implement a parse() method that returns a dictionary object containing parsed items. Users can develop their own parsers and add them to instances of the filingDocument class using the parser attribute.
