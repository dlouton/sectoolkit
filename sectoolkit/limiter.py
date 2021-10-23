from time import time, sleep
from collections import deque


class rate_limiter(object):
    
    """
    Implements a rate limiter for use in restricting the rate of file requests submitted to the SEC website.

    Arguments:

    interval :  limit interval in seconds
    limit    :  rate limit

    Usage:
    
    limiter = rate_limiter(limit_interval, max_requests_per_interval)

    if limiter.allow():
        # Submit file request
    
    """
    
    def __init__(self, interval, limit):
        self.interval = interval
        self.limit = limit
        self.req_times = deque([time() - interval], maxlen = limit)
        
    def allow(self, verbose = False):
        """
        Returns True if within the rate limit, or blocks until within limit and then returns True.
        """
        delay = self.interval - (time() - self.req_times[0])
        if delay > 0:
            if verbose:
                print("waiting... ", delay)
            # Block until we can request without exceeding the limit.
            sleep(delay)
            
        self.req_times.append(time())
            
        return True