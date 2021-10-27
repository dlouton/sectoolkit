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
from datetime import timedelta

# Sub-package imports
from .config import default_datadir, sec_base_url, binary_file_types
from .utils import seclimiter, timer, fetch_sec_file
from .secmeta import headerfile
from .formparsers import parsers


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
	parse():
		Returns a dictionary of parsed items if there is a registered parser for the document
		file type.
	"""

	
	def __init__(self, fileName, fileType, sequence, description, bsFileContent):

		self.filename = fileName
		self.type = fileType
		self.sequence = sequence
		self.description = description
		self.body = bsFileContent
		self.parser = ''
		self.parsed = {}


	def parse(self, **kwargs):

		# First check to see whether a custom parser has been specified in the self.parser instance variable.
		if self.parser != '':
			return self.parser.parse()
		elif self.type in parsers.keys():
			# Instantiate a defualt parser if one is available for this form type, passing in any kwargs that 
			# may be required or useful.
			self.parser = parsers[self.type](self.body, **kwargs)
			# Call the parser's parse() function to do the actual work. 
			self.parsed = self.parser.parse()
			return self.parsed
		else:
			# If no parser is available, inform the user of the situation.				
			print('Unable to parse {} file.  This is not a supported form type.'.format(self.type))
			return None


		
class filingArchive(object):

	"""
	Provides an interface to an SEC filing archive containing files related to a specific filing listed
	in the SEC index. 


	Required arguments:
	
	sec_filepath 	: 	path to the filing archive as shown in its SEC index file entry.
	user_agent 		:   (default = None) The SEC requires that all files requests contain a header specifying
                    	a user agent string of the form "<Company or institution name>, <contact email>".  See 
                    	the SEC developer page for further details: https://www.sec.gov/os/accessing-edgar-data

    Optional arguments:

    datadir             :   (default creates 'secdata' subdirectory under the current directory)  This is 
                            where locally cached SEC files will be stored.
    rate_limiter        :   (defaults to rate_limiter class provided in limiter sub-package)
    binary_file_types   :   (defaults to ['gz', 'zip', 'Z'])
    
		
	"""

	def __init__(self, sec_filepath, datadir = default_datadir, ratelimiter = seclimiter, \
		user_agent = None, binary_file_types = ['gz', 'zip', 'Z']):
		self.user_agent = user_agent
		self.binary_types = binary_file_types
		self.limiter = ratelimiter
		self.sec_filepath = sec_filepath
		self.header = headerfile(self.sec_filepath, datadir = datadir, user_agent = self.user_agent).get_headerDict()
		self.filingURL = sec_base_url + self.sec_filepath
		self.filingsdir = datadir + os.sep + 'filings'
		_, _, cik, fname = self.sec_filepath.split('/')
		self.localfilename = os.sep.join([self.filingsdir, cik, fname])
		self.indexURL = self.filingURL.rstrip('.txt')+'-index.html'
		self.files = []
		self.acceptance_datetime = ''


	def browse(self):
		"""
		Opens a browser window in the SEC subdirectory where items related to the filing are stored.
		"""
		wb.open(self.indexURL)
  
	
	def check_localfile(self):
		"""
		Verify that file is present in the local cache.
		"""
		return os.path.exists(self.localfilename)

	
	def get_filingArchive(self, document_types = 'ALL', text_only = True, verbose = False):
		"""
		Retrieves and parses the archive file and creates a collection of filing document objects 
		exposing the documents contained in the archive.
		"""

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
		"""
		Returns a list of files contained within the filing archive.
		"""
		if any(self.files):
			filenames = []
			for file in self.files:
				filenames.append(file.filename)
		return filenames


