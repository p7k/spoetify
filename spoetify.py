from itertools import izip, tee
import networkx import DiGraph, shortest_path
from spotimeta import search_track

cache = {}

def term_conditioner(term):
    return term.lower()

def query(term):
    term = term_conditioner(term)
    has_results = False
    if not cache.has_key(term):
        response = search_track(term)
        result = response['result']
        if result:
            has_results = True
            for track in result:
                name = track['name'].lower()
                cache[name] = track
    else:
        print 'cache hit'
    exact_match = cache.get(term)
    return has_results, exact_match

def investigate(words):
    graph = nx.DiGraph()
    n = len(words) 
    for start in range(n):
        for stop in range(start + 1, n):
            chunk = words[start:stop + 1]
            term = " ".join(chunk)
            has_results, exact_match = query(term)
            if not (has_results or exact_match):
                break
            elif exact_match:
                graph.add_edge(start, stop + 1, track=exact_match)
    return graph


def process_text(line):
    return line.strip()

if __name__ == '__main__':
    import fileinput
    input_parts = []
    for line in fileinput.input():
        input_parts.append(process_text(line))
    input_string = u' '.join(input_parts)
    print 'Your input: ' + input_string
    # investigate()
