from bs4 import BeautifulSoup
import urllib
import pandas as pd
from time import time
import re
import os
import os.path
import sys
import pathlib
import webbrowser as wb
# import multiprocessing as mp
from datetime import timedelta

# Sub-package imports
from .config import default_datadir, sec_base_url, binary_file_types
from .utils import seclimiter, timer, fetch_sec_file
from .secmeta import headerfile
from .formparsers import parsers


# Read locally cached CIK, ticker and company name file, or fetch it from the SEC website.
company_tickers_filename = '.' + os.sep + 'secdata' + os.sep + 'company_tickers.p'
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



class filingDocument(object):

	
	"""
	This class represents an SEC filing document contained within a single filing archive file. 

	...

	Attributes
	----------
	filename : str
		name of the file as it would appear on the SEC website
	type : str
		file type field as shown in the SEC filing archive file
	sequence : int
		sequence number of the document in the file - normally the filing document comes first,
		followed by supporting exhibits, news releases, etc.
	description : str
		file description field as shown in the SEC filing archive file
	body : str
		file content - note that for binary files this field is stored in uuencoded form


	Methods
	-------
	parse(itemNumber):
		Returns a dictionary of parsed items if the document file type is supported.
	"""

	
	def __init__(self, fileName, fileType, sequence, description, bsFileContent):

		self.filename = fileName
		self.type = fileType
		self.sequence = sequence
		self.description = description
		self.body = bsFileContent
		self.parser = ''

	## Change this so that it returns a dictionary of parsed items.	
	def _parse(self):

		if self.type in parsers.keys():
			self.parser = parsers[self.type](self.body)
			return
		else:				
			print('Unable to parse {} file.  This is not a supported form type.'.format(self.type))
			return None

	## This is a temporary solution until the parse dictionary format is implemented.
	def get_item(self, itemnum):

		# Make sure the document has been parsed
		if self.parser == '':
			self._parse()
		# If the parser has been instantiated return the requested item.
		if self.parser != '':
			return self.parser.get_item(itemnum)

		
class filingArchive(object):

	"""
	This class represents an SEC filing archive file. 

	...

	Inputs
	------
	sec_filepath : str
		path to the filing archive as shown in its SEC index file entry
	datadir : str
		path to local directory where SEC related files are can be cached - default
		creates subdirectory 'secdata' under the current working directory.


	Attributes
	----------
	sec_filepath : str
		path to the file as shown in its SEC index file entry
	filingURL : str
		full URL needed to locate the archive file using a web browser
	filingsdir : str
		local directory where the cached version of the filing archive is stored
	localfilename : str
		full name and path of the locally cached archive file
	indexURL:
		URL of the SEC subdirectory where items related to the filing are stored


	Methods
	-------
	browse():
		Opens a browser window in the SEC subdirectory where items related to the filing are stored.
	get_filingArchive():
		Retrieves and parses the archive file and creates a collection of filing document objects 
		exposing the documents contained in the archive.
	get_filenames():
		Returns a list of files contained within the archive.
	"""

	def __init__(self, sec_filepath, datadir = default_datadir, ratelimiter = seclimiter, \
		user_agent = None, binary_file_types = ['gz', 'zip', 'Z']):
		self.user_agent = user_agent
		self.binary_types = binary_file_types
		self.limiter = ratelimiter
		self.sec_filepath = sec_filepath
		self.header = headerfile(self.sec_filepath, user_agent = self.user_agent).get_headerDict()
		# self.__dict__.update(self.header.get_headerDict())
		self.filingURL = sec_base_url + self.sec_filepath
		self.filingsdir = datadir + os.sep + 'filings'
		_, _, cik, fname = self.sec_filepath.split('/')
		# self.filer_cik = cik
		self.localfilename = os.sep.join([self.filingsdir, cik, fname])
		self.indexURL = self.filingURL.rstrip('.txt')+'-index.html'
		self.files = []
		self.acceptance_datetime = ''


	def browse(self):

		wb.open(self.indexURL)
  
	
	def check_localfile(self):
		return os.path.exists(self.localfilename)

	
	def get_filingArchive(self, document_types = 'ALL', text_only = True, verbose = False):

		self.doc_types = document_types
		self.text_only = text_only
	
		text_suffixes = ['txt','htm','html']

		# Read locally cached filing if it exists, or fetch the filing from the SEC website.
		try:
			if os.path.exists(self.localfilename):
				with open(self.localfilename, 'r') as f:
					# data = f.read().decode('latin-1')
					data = f.read()
			else:
				_, data = fetch_sec_file(self.filingURL, self.localfilename, content = True, \
					limiter = self.limiter, user_agent = self.user_agent, verbose = verbose)

			# Parse file content
			soup = BeautifulSoup(data, 'lxml')

			if soup.find('acceptance-datetime'):
					self.acceptance_datetime = soup.find('acceptance-datetime').contents[0].strip()[:14]

			self.files = []

			for doc in soup.find_all('document'):
				if doc.find('filename'):
					fn = doc.find('filename').contents[0].strip()
				else:
					fn = '_'
				if doc.find('type'):
					doc_type = doc.find('type').contents[0].strip()
				else:
					doc_type = '_'
				if doc.find('sequence'):
					sequence = doc.find('sequence').contents[0].strip()
				else:
					sequence = '_'
				if doc.find('description'):
					description = doc.find('description').contents[0].strip()
				else:
					description = '_'
				if doc.find('text'):
					text = doc.find('text')
				else:
					text = '_'
				if doc_type in self.doc_types or self.doc_types == 'ALL':
					if (fn.split('.')[-1] in text_suffixes) or not self.text_only:
						self.files.append(filingDocument(fn, doc_type, sequence, description, text))

			if verbose:
				for f in self.files:
					print(f.filename, f.type)
					
		except: # catch *all* exceptions
			print(self.localfilename, self.filingURL)
			e = sys.exc_info()[0]
			print("Error: %s" % e)


	def get_filenames(self):
		if any(self.files):
			filenames = []
			for file in self.files:
				filenames.append(file.filename)
		return filenames


