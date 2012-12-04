import gevent
from gevent import monkey; monkey.patch_socket()
from networkx import DiGraph, shortest_path
from spotimeta import search_track
from util import pairwise, process_text, term_conditioner, throttle
from itertools import izip_longest


CACHE = {}

# TODO cache by term also - repeating substrings
# TODO cache only useful stuff | if the track name is a substring of a poem
# TODO there could be multiple title matches - perhaps, should
# make them all available - maybe even tweak by popularity or genre
@throttle(1/10.)
def query(term, s):
    term = term_conditioner(term)
    has_results = False
    if not CACHE.has_key(term):
        response = search_track(term)
        result = response['result']
        if result:
            has_results = True
            for track in result:
                name = track['name'].lower()
                CACHE[name] = track
    # else:
        # print 'cache hit'
    exact_match = CACHE.get(term)
    return has_results, exact_match, s


def slicer(iterable, start):
    for stop in range(start, len(iterable)):
        yield slice(start, stop + 1)

# TODO parallelize querying by word and it's right-side neighbors | gevent
def build_graph(words):
    """Returns a graph of substrings.
    Nodes are indices of super string array (implicit).
    Edges are substring matches (explicit).
    Generator function given ex. ['do', 're', 'mi', 'fa', 'sol'], produces the
    following:  do                  re              mi          fa      sol
                do re               re mi           mi fa       fa sol
                do re mi            re mi fa        mi fa sol
                do re mi fa         re mi fa sol
                do re mi fa sol
    """
    graph = DiGraph()
    slicers = [slicer(words, i) for i in range(len(words))]
    rounds = izip_longest(*slicers)
    for r in rounds:
        queries = []
        for s in r:
            if not s is None:
                term = (' '.join(words[s]))
                queries.append(gevent.spawn(query, term, s))
        gevent.joinall(queries)
        values = (query.value for query in queries)
        for has_results, exact_match, s in values:
            if exact_match:
                graph.add_edge(s.start, s.stop, track=exact_match)
    return graph

# TODO better exception handling
# TODO logging
def build_playlist(graph, words):
    playlist = []
    if len(graph) > 0:
        try:
            path = shortest_path(graph, 0, len(words))
        except:
            raise SystemExit
        for start, stop in pairwise(path):
            track = graph.edge[start][stop]['track']
            playlist.append((track['name'], track['artist']['name'],
                track['href']))
    return playlist


# TODO turn this thing into a webapp :)
def print_playlist(playlist):
    for track in playlist:
        print "{!s:<20} by {!s:<30} {!s:<30}".format(*track)


# TODO improve text conditioning
if __name__ == '__main__':
    import fileinput
    input_parts = []
    for line in fileinput.input():
        input_parts.append(process_text(line))
    input_string = u' '.join(input_parts)
    words = input_string.split()
    graph = build_graph(words)
    playlist = build_playlist(graph, words)
    if not playlist:
        raise SystemExit
    print_playlist(playlist)

