from itertools import izip, tee
import re
import string
import gevent
from gevent.queue import Queue

def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def throttle(interval):
    """Decorates a Greenlet function for throttling.

    Args:
        interval: time in seconds (or fractions thereof) to idle.
    """
    tq = Queue(1)
    tq.put(1)
    def _throttle(func):
        def wrapper(*args, **kwargs):
            tq.get()
            gevent.sleep(interval)
            tq.put(1)
            return func(*args, **kwargs)
        return wrapper
    return _throttle

punctuation_sans_apostrophe = re.compile('[{!s}]'.format(
    re.escape(string.punctuation.replace("'",""))))

def process_text(text):
    return punctuation_sans_apostrophe.sub(' ', text.strip())

def term_conditioner(term):
    return term.lower()
