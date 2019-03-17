from queue import Queue


class Frontier(object):
    def __init__(self):
        self.frontier = Queue()
        self.already_added = set()
        self.disallowed_urls = set()

    def get_next(self):
        return self.frontier.get()

    def is_empty(self):
        return self.frontier.empty()

    def add_url(self, url):
        if url not in self.already_added:
            if url not in self.disallowed_urls:
                self.frontier.put(url)
                self.already_added.add(url)

    def add_disallowed_url(self, url):
        self.disallowed_urls.add(url)


frontier = Frontier()


def get_next():
    url = frontier.get_next()
    return url


def is_not_empty():
    return not (frontier.is_empty())


def add_url(url):
    frontier.add_url(url)


def add_disallowed_url(url):
    frontier.add_disallowed_url(url)


def plant_seeds():
    frontier.add_url("http://www.e-prostor.gov.si/")
    frontier.add_url("http://www.sova.gov.si/")
    frontier.add_url("http://www.sova.gov.si/si/delovno_podrocje/")
    frontier.add_url("http://www.arso.gov.si/")
    frontier.add_url("http://www.evem.gov.si/")
    frontier.add_url("http://www.e-uprava.gov.si/")
    frontier.add_url("https://podatki.gov.si/")
    frontier.add_url("http://www.upravneenote.gov.si/")
    frontier.add_url("http://prostor3.gov.si/javni/login.jsp?jezik=sl")
    frontier.add_url("http://www.mju.gov.si/")
