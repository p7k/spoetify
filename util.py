from itertools import izip, tee


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

def process_text(text):
    return text.strip()

def term_conditioner(term):
    return term.lower()
