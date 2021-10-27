
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