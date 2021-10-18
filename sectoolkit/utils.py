import urllib.request
import pathlib
import re
import os
import xmltodict
from time import time

from .config import default_datadir, sec_base_url, binary_file_types, sec_rate_limit, sec_rate_interval
from .limiter import rate_limiter

# Instantiate rate_limiter
seclimiter = rate_limiter(sec_rate_interval, sec_rate_limit)


def timer(method):
    def wrapper(*args, **kwargs):
        start_time = time()
        result = method(*args, **kwargs)
        end_time = time()
        elapsed = end_time - start_time
        if elapsed < 60:
            print('Time elapsed: ', elapsed, ' seconds.')
        else:
            print('Time elapsed: ', elapsed/60, ' minutes.')
        return result
    return wrapper


def fetch_sec_file(url, localpath, limiter = seclimiter, user_agent = None, content = False, verbose = False):
		
	# Setup request headers as required by SEC
	req = urllib.request.Request(url)
	if user_agent != None:
		req.add_header("User-Agent", user_agent)
	else:
		"The SEC requires a User-Agent definition of the form <Company Name admin@company.com>"
	# Restore gzip header after decode on read issue has been resolved
	# req.add_header("Accept-Encoding", "gzip, deflate")
	req.add_header("Host", "www.sec.gov")
	
	# Make sure that the directory path exists
	path = pathlib.Path(localpath)
	path.parent.mkdir(parents=True, exist_ok=True)
	
	try:
		if limiter.allow(verbose = verbose):
			with urllib.request.urlopen(req) as response:
				data = response.read()
				if url.split('.')[-1] in binary_file_types:
					with open(localpath, 'wb') as f:
						f.write(data)
				else:
					with open(localpath, 'w') as f:
						data = data.decode('latin-1')
						f.write(data) 
		  
		if verbose:
			print(localpath)
		if content:
			return localpath, data
		else:
			return localpath
				
	except Exception as inst:
		print(url)
		print(localpath)
		print(inst)          # the exception instance
		print(inst.args)     # arguments stored in .args

