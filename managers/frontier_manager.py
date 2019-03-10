from queue import Queue


class Frontier(object):
    def __init__(self):
        self.frontier = Queue()

    def get_next(self):
        return self.frontier.get()

    def is_empty(self):
        return self.frontier.empty()

    def add_url(self, url):
        self.frontier.put(url)


frontier = Frontier()
visited = set()


def get_next():
    url = frontier.get_next()
    visited.add(url)
    return url


def is_not_empty():
    return not (frontier.is_empty())


def add_url(url):
    # to prevent duplicates
    if url not in visited:
        frontier.add_url(url)


def plant_seeds():
    frontier.add_url("http://www.sova.gov.si/")
    frontier.add_url("http://www.arso.gov.si/")
    frontier.add_url("http://www.evem.gov.si/")
    frontier.add_url("http://www.e-uprava.gov.si/")
    frontier.add_url("http://www.podatki.gov.si/")
    frontier.add_url("http://www.upravneenote.gov.si/")
    frontier.add_url("http://prostor3.gov.si/javni/login.jsp?jezik=sl")
    frontier.add_url("http://www.mju.gov.si/")

# todo consider about locking url
# class FrontierElement(object):
