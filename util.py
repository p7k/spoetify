from itertools import izip, tee
import re
import string

punctuation_sans_apostrophe = re.compile('[{!s}]'.format(
    re.escape(string.punctuation.replace("'",""))))

def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def process_text(text):
    return punctuation_sans_apostrophe.sub(' ', text.strip())

def term_conditioner(term):
    return term.lower()
