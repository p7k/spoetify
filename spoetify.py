from gevent import spawn, joinall
from gevent import monkey; monkey.patch_socket()
from networkx import DiGraph, shortest_path
from spotimeta import search_track
from util import pairwise, process_text, term_conditioner, throttle
from functools import partial


CACHE = {}

# TODO proper caching and invalidation based on response headers
# TODO cache by term also - repeating substrings
# TODO cache only useful stuff | if the track name is a substring of a poem
# TODO there could be multiple title matches - perhaps, should
# make them all available - maybe even tweak by popularity or genre
@throttle(1./10)
def query(term):
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
    exact_match = CACHE.get(term)
    return has_results, exact_match


def slicer(sequence, start):
    """Returns a generator of incremental :slice: objects to a sequence from a
    'start' index.
    """
    for stop in range(start, len(sequence)):
        yield slice(start, stop + 1)


def fetcher(graph, words, n):
    """Fetch results for incremental slices and decide whether or not to
    continue.  If a smaller slice from a particular position can't be found,
    there's no sense in trying larger slices.
    If there's an exact match for the substring, an edge is added to the graph.
    """
    for s in slicer(words, n):
        term = ' '.join(words[s])
        g = spawn(query, term)
        g.join()
        has_results, exact_match = g.value
        if not (has_results or exact_match):
            break
        elif exact_match:
            graph.add_edge(s.start, s.stop, track=exact_match)


def build_graph(words):
    """Returns a graph of substrings.
    Nodes are indices of super string array (implicit).
    Edges are substring matches (explicit).
    Spawns parallel 'fetchers' for every word which handle incremental slices.
    Example:    ['do', 're', 'mi', 'fa', 'sol'],
                do                  re              mi          fa      sol
                do re               re mi           mi fa       fa sol
                do re mi            re mi fa        mi fa sol
                do re mi fa         re mi fa sol
                do re mi fa sol
    """
    graph = DiGraph()
    joinall([spawn(fetcher, graph, words, n) for n in range(len(words))])
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
def spoetify(text):
    words = input_string.split()
    graph = build_graph(words)
    playlist = build_playlist(graph, words)
    if not playlist:
        raise SystemExit
    print_playlist(playlist)


if __name__ == '__main__':
    import fileinput
    input_parts = []
    for line in fileinput.input():
        input_parts.append(process_text(line))
    input_string = u' '.join(input_parts)
    spoetify(input_string)
