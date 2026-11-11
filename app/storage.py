users = {}
movies = {}
reviews = {}
watchlist = {}
tokens = {}

counters = {
    "user": 0,
    "movie": 0,
    "review": 0,
    "watchlist": 0,
    }

def next_id(name):
    counters[name] += 1
    return counters[name]