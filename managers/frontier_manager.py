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
        if url.url not in self.already_added:
            if url.url not in self.disallowed_urls:
                self.frontier.put(url)
                self.already_added.add(url)

    def add_disallowed_url(self, url):
        self.disallowed_urls.add(url)

    def is_disallowed_url(self, url):
        for el in self.disallowed_urls:
            if el in url or url in el:
                return True
        return False


class ScrapUrl(object):
    def __init__(self, parent, url):
        self.parent = parent
        self.url = url


frontier = Frontier()


def get_next():
    url = frontier.get_next()
    return url


def is_not_empty():
    return not (frontier.is_empty())


def add_url(parent_url, url):
    frontier.add_url(ScrapUrl(parent_url, url))


def add_disallowed_url(url):
    frontier.add_disallowed_url(url)


def plant_seeds():
    frontier.add_url(ScrapUrl("", "https://e-uprava.gov.si/"))
    frontier.add_url(ScrapUrl("", "http://www.e-prostor.gov.si/"))
    frontier.add_url(ScrapUrl("", "http://www.sova.gov.si/"))
    frontier.add_url(ScrapUrl("", "http://www.sova.gov.si/si/delovno_podrocje/"))
    frontier.add_url(ScrapUrl("", "http://www.arso.gov.si/"))
    frontier.add_url(ScrapUrl("", "https://podatki.gov.si/"))
    frontier.add_url(ScrapUrl("", "http://www.upravneenote.gov.si/"))
    frontier.add_url(ScrapUrl("", "http://prostor3.gov.si/javni/login.jsp?jezik=sl"))
    frontier.add_url(ScrapUrl("", "http://www.mju.gov.si/"))
