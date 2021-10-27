import os

# Config items
default_datadir = '.' + os.sep + 'secdata'
sec_base_url = 'https://www.sec.gov/Archives/'
binary_file_types = ['gz', 'zip', 'Z']
sec_rate_limit = 8   # maximum downloads per rate interval
sec_rate_interval = 1.0  # rate interval in seconds