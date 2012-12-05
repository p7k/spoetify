from itertools import izip, tee
import re
import string
import gevent
from gevent.queue import Queue
from timeit import default_timer

def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def gevent_throttle(calls_per_sec=0):
    """Decorates a Greenlet function for throttling."""
    interval = 1. / calls_per_sec if calls_per_sec else 0
    def decorate(func):
        tq = Queue(1)
        tq.put(0.)
        def throttled_func(*args, **kwargs):
            if calls_per_sec:
                last, current = tq.get(), default_timer()
                elapsed = current - last
                if elapsed < interval:
                    gevent.sleep(interval - elapsed)
                tq.put(default_timer())
            return func(*args, **kwargs)
        return throttled_func
    return decorate

punctuation_sans_apostrophe = re.compile('[{!s}]'.format(
    re.escape(string.punctuation.replace("'",""))))

def process_text(text):
    return punctuation_sans_apostrophe.sub(' ', text.strip())

def term_conditioner(term):
    return term.lower()
