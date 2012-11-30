from networkx import DiGraph, shortest_path
from spotimeta import search_track
from util import pairwise, process_text, term_conditioner


CACHE = {}

# TODO cache by term also - repeating substrings
# TODO cache only useful stuff | if the track name is a substring of a poem
# TODO there could be multiple title matches - perhaps, should
# make them all available - maybe even tweak by popularity or genre
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
    # else:
        # print 'cache hit'
    exact_match = CACHE.get(term)
    return has_results, exact_match


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
    n = len(words)
    for start in range(n):
        for stop in range(start + 1, n):
            chunk = words[start:stop + 1]
            term = ' '.join(chunk)
            has_results, exact_match = query(term)
            if not (has_results or exact_match):
                break
            elif exact_match:
                graph.add_edge(start, stop + 1, track=exact_match)
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

