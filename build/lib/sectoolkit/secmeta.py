import pandas as pd
import datetime
import urllib
import urllib.request
import os.path
import pathlib
import xmltodict
import json
from tqdm.notebook import tqdm
import multiprocessing as mp 
import re

from .config import default_datadir, sec_base_url, binary_file_types
from .utils import seclimiter, timer, fetch_sec_file


class idx(object):

    """
    Provides an interface to the SEC's collection of quarterly index files.


    Required arguments:

    user_agent :    (default = None) The SEC requires that all files requests contain a header specifying
                    a user agent string of the form "<Company or institution name>, <contact email>".  See 
                    the SEC developer page for further details: https://www.sec.gov/os/accessing-edgar-data

    Optional arguments:

    datadir             :   (default creates 'secdata' subdirectory under the current directory)  This is 
                            where locally cached SEC files will be stored.
    start_year          :   (default = 1993 specifies the start of the SEC's online filing collection)
    start_quarter       :   (default = 1)
    end_year            :   (default = 0 specifies the current year)
    end_quarter         :   (default = 4)
    rate_limiter        :   (defaults to rate_limiter class provided in limiter sub-package)
    binary_file_types   :   (defaults to ['gz', 'zip', 'Z'])

    """
    
    
    def __init__(self, datadir = default_datadir, start_year = 1993, \
                 start_quarter = 1, end_year = 0, end_quarter = 4, \
                 rate_limiter = seclimiter, \
                 user_agent = None, binary_file_types = binary_file_types):
        self.user_agent = user_agent
        self.binary_types = binary_file_types
        self.datadir = datadir
        self.idxdir = os.path.join(self.datadir, 'idxfiles')
        self.hdrdir = os.path.join(self.datadir, 'headerfiles')
        self.filingsdir = os.path.join(self.datadir, 'filings')
        self.parsed_header_cache = os.path.join(self.datadir, 'parsed_header_cache.p')
        self.sec_base = sec_base_url
        self.limiter = rate_limiter
        self.beg_yr = start_year
        self.beg_qtr = start_quarter
        self.end_yr = end_year
        self.end_qtr = end_quarter
        self.idxlist = self.updateidx()
        self.hdrlist = []
        self.filinglist = []
        self.localparsed = []
        self.working_idx = pd.DataFrame() # initialize as empty dataframe to avoid exceptions
        self.working_paths = []
        
        
    def _idxurls(self):
        """
        Creates a list of URLs for the SEC quarterly index files included in the date range 
        specified by the instance beg_yr, beg_qtr, end_yr and end_qtr variables.
        """
        ## Need to add some type checking and bounds checking on input parameters
        if self.end_yr == 0:
            self.end_yr = datetime.date.today().year
            current_qtr = (datetime.date.today().month - 1) // 3 + 1
            if self.end_qtr > current_qtr:
                self.end_qtr = current_qtr
        yq = []
        for y in range(self.beg_yr, self.end_yr + 1):
            bq, eq = 1, 4
            if y == self.beg_yr:
                bq = self.beg_qtr
            if y == self.end_yr:
                eq = self.end_qtr
            for i in range(bq, eq + 1):
                yq.append([y,i])  
        return ['https://www.sec.gov/Archives/edgar/full-index/%d/QTR%s/master.gz' % (x[0], x[1]) for x in yq]

                
    def _filter_index_file(self, file, filters, verbose = False):
        """
        Apply row filters specified in filters dictionary to a particular index file.  An empty filter
        dictionary will return the entire index file.

        Note: Filtering on date ranges is not yet supported.
        """
        if verbose:
            print(file, '\n')
        df = pd.read_csv(file, sep = '|', skiprows = 9, compression = 'gzip', \
        	parse_dates = [3], encoding = 'latin-1', low_memory = False)
        df.dropna(inplace = True)
        # Apply filters
        ## More work needed on this section to support filtering on date ranges
        ## and fuzzy matching on company names
        for key in filters.keys():
            df = df[df[key].isin(filters[key])]
        return df


    def _clear_local_cache(self, localdir, suffix = None):
        """
        Deletes all locally cached SEC files.
        """
        for root, dirs, files in os.walk(localdir, topdown=False):
            for fname in files:
                fpath = (os.sep).join([root, fname])
                if suffix:
                    if fname.endswith(suffix):
                        os.remove(fpath)
                else:
                    os.remove(fpath)
            for dname in dirs:
                dpath = (os.sep).join([root, dname])
                if not os.listdir(dpath):
                    os.rmdir(dpath)
      
    
    def _catalog_local_files(self, localdir, suffix = None):
        localfiles = []
        for root, dirs, files in os.walk(localdir, topdown=False):
            for fname in files:
                fpath = os.sep.join([root, fname])
                if suffix:
                    if fname.endswith(suffix):
                        localfiles.append(fpath)
                else:
                    localfiles.append(fpath)
        return localfiles
    
    
    def _convert_sec_filename(self, sec_filename):
        """
        Accepts SEC filepath as input and returns retrieval URL for SGML header file and 
        local filepath where header file may be cached.
        """
        _, _, cik, fname = sec_filename.split('/')
        fname_body = fname.split('.')[0]
        new_fname = fname_body+'.hdr.sgml'
        hdrfilepath = os.sep.join([self.hdrdir, cik, new_fname])
        url = self.sec_base+'/'.join([cik, ''.join(fname_body.split('-')), new_fname])
        return url, hdrfilepath
    
    
    def _get_working_paths(self):
        """
        Creates a list of SGML headerfile URL and local file path tuples for all filings included in the 
        current working_idx of filings.
        """
        if len(self.working_idx) == 0:
            print("Run filter_index() first...")
            return []
        else:
            working_paths = []
            for file in list(self.working_idx.Filename):
                working_paths.append(self._convert_sec_filename(file))
            return working_paths
    

    def _process_files(self, function, filelist, func_args, max_processes = 0, \
                       verbose = False):
        """
        This utility function makes use of multiple CPU cores to run the same function on multiple
        input files.  It returns function output to the calling function in list form for aggregation.

        """
        
        files = [x for x in filelist if x != None]
        completed = []
        inprocess = []
        if mp.cpu_count() <= max_processes or max_processes == 0:
            nprc = mp.cpu_count()
        else:
            nprc = max_processes
        if verbose:
            print('Processing {} files ...'.format(len(files)))
            print('Number of CPUs: ', nprc)
        with mp.Pool(processes = nprc) as pool:
            for file in files:
                r = pool.apply_async(function, (file, *func_args), \
                                     callback=completed.append)
                inprocess.append(r)
            for r in inprocess:
                r.wait()
        if verbose:
            print('Finished processing files.')
            
        return completed
                
            
    @timer
    def updateidx(self, verbose = False):
        """
        Updates the locally cached quarterly index files for the date range specified in the instance dict.
        By default the most recent quarterly index file included in the local cache is deleted and replaced 
        by the most current version available from the SEC website.

        """
        
        print("Updating locally cached SEC index files...")
        
        # Catalog locally saved index files
        idxlocal = self._catalog_local_files(self.idxdir, suffix = 'gz')
        
        # Drop the most recently saved idx file since it may be incomplete.
        if len(idxlocal) > 0:
            idxlocal.sort()
            last = idxlocal.pop()
            os.remove(last)
        else:
            print("You don't seem to have any SEC index files cached in your data directory.")
            print("Downloading these files for the first time may take 1-4 minutes.")

        # Fetch any missing idxfiles
        idxlist = []
        ## Need to fix first day of the quarter problem with self._idxurls()
        ## Speed this loop up by using multi-processing ?
        for url in tqdm(self._idxurls()):
            idxpath = self.idxdir+os.sep+os.sep.join(url.split('/')[-3:])
            if idxpath not in idxlocal:
                path = pathlib.Path(idxpath)
                path.parent.mkdir(parents=True, exist_ok=True)
                ## Need to add some checks here to flag download errors
                ## Also need to find a better way to do this since urlretrieve 
                ## is slated for deprecation
                fname = fetch_sec_file(url, idxpath, user_agent = self.user_agent, verbose = verbose)
            idxlist.append(idxpath)
            
        return idxlist
       
    
    def show_index_fields(self):
        """
        Return index file column names and data types.
        """
        df = pd.read_csv(self.idxlist[-1], sep = '|', skiprows = 9, compression = 'gzip', \
        	parse_dates = [3], encoding = 'latin-1', low_memory = False, nrows = 5)
        return df.dtypes
    
    
    def index_peek(self, rows = 5):
        """
        Read the a specified number of rows from the index file for the most recent quarter in the date range
        specified in the instance dict.
        """
        df = pd.read_csv(self.idxlist[-1], sep = '|', skiprows = 9, compression = 'gzip', \
        	parse_dates = [3], encoding = 'latin-1', low_memory = False)
        return df.tail(rows)
    

    @timer
    def filter_index(self, filters = {}, verbose = False):
        """
        Apply filters to the full set of index files for the date range specified in the index dict
        to create a working index.

        Arguments:

        filters     :   (default = {})  Specify a dictionary containing column specific row filters to 
                        be applied to the index files.
        verbose     :   (default = False)

        """
        
        # Initialize a dataframe that will contain filtered index records
        self.working_idx = pd.DataFrame()
        
        # Run filters on index files
        ## Need to improve this to allow for interactive, iterative, filtering.
        print('Filtering {} quarterly index files ...'.format(len(self.idxlist)))
        filter_results = self._process_files(self._filter_index_file, self.idxlist, (filters,))
        self.working_idx = pd.concat([x for x in filter_results if len(x) != 0]) 
        print("Filtered index contains ", len(self.working_idx), " records.")
        
        return self.working_idx

    
    def fetch_header_files(self, sec_proc_max = 0, verbose = False):
        """
        Fetch any SGML header files for the current working index that are not already present in the
        local cache.
        """
        
        if len(self.working_idx) == 0:
            print("Run filter_index() before fetch_header_files()...")
            return
                            
        # Make sure that we have relevant paths for files in self.working_idx
        if len(self.working_paths) == 0:
            self.working_paths = self._get_working_paths()
           
        # Determine whether additional header files need to be fetched from the SEC
        fetchnum = 0
        self.hdrlist = []
        for file in list(self.working_idx.Filename):
            hdr = headerfile(file, datadir = self.datadir, user_agent = self.user_agent)
            if not hdr.islocal:
                fetchnum += 1
            self.hdrlist.append(hdr)
        
        # Fetch any additional header files that are needed - single threaded because of SEC rate limit.
        if fetchnum != 0:
            print('Fetching {} header files ...'.format(fetchnum))
            for item in self.hdrlist:
                if not item.islocal:
                    item.fetch_file(verbose = True)
            print('Finished fetching header files.')
        else:
            print('All header files are present in the local cache.')


    def fetch_filings(self, sec_proc_max = 0, verbose = False):
        """
        Fetch any filing archives files included in the current working index if they are not already 
        present in the local file cache.
        """
        
        if len(self.working_idx) == 0:
            print("Run filter_index() before fetch_filings()...")
            return

        # Make sure that we have URLs and local filepaths for all filing archives in self.working_idx.
        filing_paths = []
        for sec_filepath in list(self.working_idx.Filename):
            filingURL = self.sec_base + sec_filepath
            _, _, cik, fname = sec_filepath.split('/')
            localfilepath = os.sep.join([self.filingsdir, cik, fname])
            filing_paths.append((filingURL, localfilepath))
           
        # Determine whether additional filing archives need to be fetched from the SEC
        fetchnum = 0
        fetchlist = []
        self.filinglist = []
        for item in filing_paths:
            if not os.path.exists(item[1]):
                fetchnum += 1
                fetchlist.append(item)
            else:
                self.filinglist.append(item[1])
        
        # Fetch any additional filing archives that are needed - single threaded because of SEC rate limit.
        if fetchnum != 0:
            print('Fetching {} filing archives ...'.format(fetchnum))
            for item in fetchlist:
                fetch_sec_file(item[0], item[1], user_agent = self.user_agent, verbose = True)
            print('Finished fetching filing archives.')
        else:
            print('All filing archives are present in the local cache.')


    def clear_index_cache(self):
        """
        Delete locally cached SEC index files.
        """
        self._clear_local_cache(self.idxdir)
        # Reset idxlist to an empty list since we have deleted the cached index files
        self.idxlist = []
    
    
    def clear_header_cache(self):
        """
        Delete locally cached SGML header files.
        """
        self._clear_local_cache(self.hdrdir)
        # Reset hdrlist to an empty list since we have deleted the cached index files
        self.hdrlist = []



class headerfile(object):

    """
    Provides an interface to the SGML header file that provides meta data for a specific SEC filing.


    Required arguments:

    sec_filename    :   The SEC filepath specified in the last field of the index record for the filing. 
    user_agent      :   (default = None) The SEC requires that all files requests contain a header specifying 
                        a user agent string of the form "<Company or institution name>, <contact email>".  
                        See the SEC developer page for further details: https://www.sec.gov/os/accessing-edgar-data

    Optional arguments:

    datadir             :   (default creates 'secdata' subdirectory under the current directory)  This is 
                            where locally cached SEC files will be stored.
    rate_limiter        :   (defaults to rate_limiter class provided in limiter sub-package)

    """
    
    
    def __init__(self, sec_filename, datadir = default_datadir, \
                 rate_limiter = seclimiter, \
                 user_agent = None):
        self.user_agent = user_agent
        self.limiter = rate_limiter
        self.datadir = datadir
        self.hdrdir = os.path.join(self.datadir, 'headerfiles')
        self.sec_base = 'http://www.sec.gov/Archives/edgar/data/'
        self.url, self.localpath = self._convert_sec_filename(sec_filename)
        self.islocal = os.path.exists(self.localpath)
        

    ## This should be pulled out as a standalone function since it is needed by both idx and headerfile classes.
    def _convert_sec_filename(self, sec_filename):
        """
        Accepts SEC filepath as input and returns retrieval URL for SGML header file and local filepath
        where header file may be cached.
        """
        _, _, cik, fname = sec_filename.split('/')
        fname_body = fname.split('.')[0]
        new_fname = fname_body+'.hdr.sgml'
        hdrfilepath = os.sep.join([self.hdrdir, cik, new_fname])
        url = self.sec_base+'/'.join([cik, ''.join(fname_body.split('-')), new_fname])
        return url, hdrfilepath
        
    
    def _SGMLfiletoDict(self):
        """
        Reads an SGML header file and converts it to a Python dictionary.
        """
        end_tags = []
        xmlstring = ''
        tag = re.compile("<.[^(><.)]+>")
        with open(self.localpath, 'r', encoding = 'latin-1') as f:
            xmlstring += '<?xml version="1.0"?>'+'\n'
            lines = f.read().splitlines()
            # Identify containers
            for line in lines:
                if line.startswith("</"):
                    end_tags.append(line)
            container_tags = [s.replace('/', '') for s in end_tags] + end_tags
            # Add closing tags for non-container fields
            for line in lines:
                a = re.findall(tag, line)
                if len(a) > 0:
                    if a[0] in container_tags:
                        xmlstring += line+'\n'
                    else:
                        xmlstring += line.replace("&", "and") + a[0][:1]+'/'+a[0][1:]+'\n'
        return xmltodict.parse(xmlstring)['SEC-HEADER']


    def get_headerDict(self, verbose = False):
        """
        Returns the contents of the SGML header file in dictionary form.
        """

        if not self.islocal:
            self.fetch_file(verbose = verbose)

        return self._SGMLfiletoDict()
    
    
    def fetch_file(self, content = False, verbose = False):
        """
        Downloads the SGML header file from the SEC website.

        """
            
        _ = fetch_sec_file(self.url, self.localpath, content = content, limiter = self.limiter, \
            user_agent = self.user_agent, verbose = verbose)
            
        return
 

