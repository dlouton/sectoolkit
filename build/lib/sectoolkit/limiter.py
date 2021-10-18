from time import time, sleep
from collections import deque


class rate_limiter(object):
    
    """
    interval :  limit interval in seconds
    limit    :  rate limit
    
    """
    
    def __init__(self, interval, limit):
        self.interval = interval
        self.limit = limit
        self.req_times = deque([time() - interval], maxlen = limit)
        
    def allow(self, verbose = False):
        delay = self.interval - (time() - self.req_times[0])
        if delay > 0:
            if verbose:
                print("waiting... ", delay)
            # Block until we can request without exceeding the limit.
            sleep(delay)
            
        self.req_times.append(time())
        
#         if verbose:
#             print(self.req_times[0])
            
        return True