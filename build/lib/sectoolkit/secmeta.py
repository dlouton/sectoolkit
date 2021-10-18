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


class meta(object):
    
    
    def __init__(self, datadir = default_datadir, start_year = 1993, \
                 start_quarter = 1, end_year = 0, end_quarter = 4, \
                 rate_limiter = seclimiter, \
                 user_agent = None, binary_file_types = binary_file_types):
        self.user_agent = user_agent
        self.binary_types = binary_file_types
        self.datadir = datadir
        self.idxdir = os.path.join(self.datadir, 'idxfiles')
        self.hdrdir = os.path.join(self.datadir, 'headerfiles')
        self.parsed_header_cache = os.path.join(self.datadir, 'parsed_header_cache.p')
        self.sec_base = sec_base_url
        self.limiter = rate_limiter
        self.beg_yr = start_year
        self.beg_qtr = start_quarter
        self.end_yr = end_year
        self.end_qtr = end_quarter
        self.idxlist = self.updateidx()
        self.hdrlist = []
        self.localparsed = []
        self.working_idx = pd.DataFrame() # initialize as empty dataframe to avoid exceptions
        self.working_paths = []
        
        
    def _idxurls(self):
        ## Need to add some type checking and bounds checking on input parameters
        if self.end_yr == 0:
            self.end_yr = datetime.date.today().year
            ## More work needed to fine tune this logic
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
        _, _, cik, fname = sec_filename.split('/')
        fname_body = fname.split('.')[0]
        new_fname = fname_body+'.hdr.sgml'
        hdrfilepath = os.sep.join([self.hdrdir, cik, new_fname])
        url = self.sec_base+'/'.join([cik, ''.join(fname_body.split('-')), new_fname])
        return url, hdrfilepath
    
    
    def _get_working_paths(self):
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
        
        files = [x for x in filelist if x != None]
#         self.pbar = tqdm(total = len(files))
#         self.results = []
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
        df = pd.read_csv(self.idxlist[-1], sep = '|', skiprows = 9, compression = 'gzip', \
        	parse_dates = [3], encoding = 'latin-1', low_memory = False, nrows = 12)
        return df.dtypes
    
    
    def index_peek(self, rows = 5):
        # Read the index file for the current quarter
        df = pd.read_csv(self.idxlist[-1], sep = '|', skiprows = 9, compression = 'gzip', \
        	parse_dates = [3], encoding = 'latin-1', low_memory = False)
        return df.tail(rows)
    
    @timer
    def filter_index(self, filters = {}, verbose = False):
        
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
        
        if len(self.working_idx) == 0:
            print("Run filter_index() before fetch_headers()...")
            return
                            
        # Make sure that we have relevant paths for files in self.working_idx
        if len(self.working_paths) == 0:
            self.working_paths = self._get_working_paths()
           
        # Determine whether additional header files need to be fetched from the SEC
        fetchnum = 0
        self.hdrlist = []
        for file in list(self.working_idx.Filename):
            hdr = headerfile(file, user_agent = self.user_agent)
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
              
    
    def clear_index_cache(self):
        self._clear_local_cache(self.idxdir)
        # Reset idxlist to an empty list since we have deleted the cached index files
        self.idxlist = []
    
    
    def clear_header_cache(self):
        self._clear_local_cache(self.hdrdir)
        # Reset hdrlist to an empty list since we have deleted the cached index files
        self.hdrlist = []



class headerfile(object):
    
    
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
        

    def _convert_sec_filename(self, sec_filename):
        _, _, cik, fname = sec_filename.split('/')
        fname_body = fname.split('.')[0]
        new_fname = fname_body+'.hdr.sgml'
        hdrfilepath = os.sep.join([self.hdrdir, cik, new_fname])
        url = self.sec_base+'/'.join([cik, ''.join(fname_body.split('-')), new_fname])
        return url, hdrfilepath
        
    
    def _SGMLfiletoDict(self):
        """
        Reads an SEC SGML header file and converts it to a JSON string.
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

        if not self.islocal:
            self.fetch_file(verbose = verbose)

        return self._SGMLfiletoDict()
    
    
    def fetch_file(self, content = False, verbose = False):
            
        _ = fetch_sec_file(self.url, self.localpath, content = content, limiter = self.limiter, \
            user_agent = self.user_agent, verbose = verbose)
            
        return
 

