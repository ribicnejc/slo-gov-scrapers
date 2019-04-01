from queue import Queue
from utils.url_helper import url_canon
from utils.url_helper import get_domain_name


class Frontier(object):
    def __init__(self):
        self.frontier = Queue()
        self.already_added = set()
        self.disallowed_urls = set()
        self.domain_wait_times = dict()  # crawlers check last access time and sleep accordingly

    def get_next(self):
        return self.frontier.get()

    def is_empty(self):
        return self.frontier.empty()

    def add_url(self, url):
        if ".gov.si" in get_domain_name(url.url):
            if url.url not in self.already_added and url.url not in self.disallowed_urls:
                self.frontier.put(url)
                self.already_added.add(url.url)

    def add_disallowed_url(self, url):
        self.disallowed_urls.add(url)

    def is_disallowed_url(self, url):
        for el in self.disallowed_urls:
            if el in url or url in el:
                return True
        return False

    def put_domain_access_time(self, domain, time):
        self.domain_wait_times[domain] = time

    def get_domain_access_time(self, domain):
        try:
            return self.domain_wait_times[domain]
        except KeyError:
            return None


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
    frontier.add_url(ScrapUrl(url_canon(parent_url), url_canon(url)))


def add_disallowed_url(url):
    frontier.add_disallowed_url(url)


def put_domain_access_time(domain, time):
    frontier.put_domain_access_time(domain, time)


def get_domain_access_time(domain):
    return frontier.get_domain_access_time(domain)


def plant_seeds():
    add_url('', "http://evem.gov.si/")
    add_url('', "https://e-uprava.gov.si/")
    add_url('', "https://podatki.gov.si/")
    add_url('', "http://www.e-prostor.gov.si/")

    # frontier.add_url(ScrapUrl("", "http://www.sova.gov.si/"))
    # frontier.add_url(ScrapUrl("", "http://www.sova.gov.si/si/delovno_podrocje/"))
    # frontier.add_url(ScrapUrl("", "http://www.arso.gov.si/"))
    # frontier.add_url(ScrapUrl("", "http://www.upravneenote.gov.si/"))
    # frontier.add_url(ScrapUrl("", "http://prostor3.gov.si/javni/login.jsp?jezik=sl"))
    # frontier.add_url(ScrapUrl("", "http://www.mju.gov.si/"))
