import gevent
from gevent import monkey; monkey.patch_socket()
from gevent.queue import Queue
from networkx import DiGraph, shortest_path
from util import pairwise, process_text, term_conditioner
import requests
import requests_cache


# request-level cache using HTTP Cache Control
requests_cache.configure('spotify_cache')
# term-level cache
_Q_CACHE = {}

def search_track_url(q, page):
    params = dict(q=q.encode('UTF-8'), page=page)
    return requests.Request("http://ws.spotify.com/search/1/track.json",
            params=params).full_url


def throttler(interval):
    throttle_queue = Queue(maxsize=1)
    throttle_queue.put(1)
    def _throttle():
        throttle_queue.get()
        gevent.sleep(interval)
        throttle_queue.put(1)
    return _throttle

# Spotify MetaAPI dictates max rate of 10 requests per second
_throttle = throttler(1./10)

# TODO timeout and exception handling
# TODO cache only useful stuff | if the track name is a substring of a poem
# TODO there could be multiple title matches - perhaps, should
# make them all available - maybe even tweak by popularity or genre
def search_track(q, page=1):
    q = term_conditioner(q)
    has_tracks = False
    if not _Q_CACHE.has_key(q):
        url = search_track_url(q, page)
        # decide if we need throttle depending on HTTP Cache vs API
        if not requests_cache.has_url(url):
            _throttle()
        response = requests.get(url).json
        tracks = response['tracks']
        has_tracks = bool(tracks)
        for track in tracks:
            name = track['name'].lower()
            _Q_CACHE[name] = track
    exact_match = _Q_CACHE.get(q)
    return has_tracks, exact_match


def slicer(sequence, start):
    """Returns a generator of incremental :slice: objects to a sequence from a
    'start' index.
    """
    for stop in range(start, len(sequence)):
        yield slice(start, stop + 1)


def _search_boss(graph, words, n):
    """Fetch results for incremental slices and decide whether or not to
    continue.  If a smaller slice from a particular position can't be found,
    there's no sense in trying larger slices.
    If there's an exact match for the substring, an edge is added to the graph.
    """
    for s in slicer(words, n):
        q = ' '.join(words[s])
        g = gevent.spawn(search_track, q)
        g.join()
        has_results, exact_match = g.value
        if not (has_results or exact_match):
            break
        elif exact_match:
            graph.add_edge(s.start, s.stop, track=exact_match)


def _build_graph(words):
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
    gevent.joinall([gevent.spawn(_search_boss, graph, words, n) for n in range(len(words))])
    return graph


# TODO better exception handling
# TODO logging
def _build_playlist(graph, words):
    playlist = []
    if len(graph) > 0:
        try:
            path = shortest_path(graph, 0, len(words))
        except:
            raise SystemExit
        for start, stop in pairwise(path):
            track = graph.edge[start][stop]['track']
            playlist.append((track['name'], track['artists'][0]['name'],
                track['href']))
    return playlist


# TODO turn this thing into a webapp :)
def _print_playlist(playlist):
    for track in playlist:
        print "{!s:<20} by {!s:<30} {!s:<30}".format(*track)


# TODO improve text conditioning
def spoetify(text):
    words = input_string.split()
    graph = _build_graph(words)
    playlist = _build_playlist(graph, words)
    if not playlist:
        raise SystemExit
    _print_playlist(playlist)


if __name__ == '__main__':
    import fileinput
    input_parts = []
    for line in fileinput.input():
        input_parts.append(process_text(line))
    input_string = u' '.join(input_parts)
    spoetify(input_string)
