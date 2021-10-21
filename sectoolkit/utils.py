import urllib.request
import pathlib
import re
import os
import xmltodict
import pandas as pd
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
		if limiter.allow(verbose = verbose) or limiter == None:
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


# Read locally cached CIK, ticker and company name file, or fetch it from the SEC website.
def get_ticker_name_dicts(datadir = default_datadir):
	company_tickers_filename = datadir + os.sep + 'company_tickers.p'
	# Check whether the local file exists and if so when it was last modified
	if os.path.exists(company_tickers_filename):
		mtime = os.path.getmtime(company_tickers_filename)
	else:
		mtime = 0.0
	# Only use the local version of the file if it is less than a day old
	if (time() - mtime)/(60*60*24) < 1.0:
		#Read the local copy of the file
		t = pd.read_pickle(company_tickers_filename)
	else:
		# Retrieve a fresh copy of the file
		t = pd.read_json('https://www.sec.gov/files/company_tickers.json').transpose()
		t['cik'] = t['cik_str'].apply(lambda x: str(x).zfill(10))
		# Make sure that the local directory path exists
		path = pathlib.Path(company_tickers_filename)
		path.parent.mkdir(parents=True, exist_ok=True)
		# Save a local copy of the file
		t.to_pickle(company_tickers_filename)

	# Setup cik->ticker and cik->company name dictionaries
	ticker_dict = dict(zip(t.cik,t.ticker))
	name_dict = dict(zip(t.cik,t.title))

	return ticker_dict, name_dict