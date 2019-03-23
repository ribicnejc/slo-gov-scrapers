from w3lib import url as w3url
from urllib.parse import urlsplit


def url_canon(url):
    return w3url.canonicalize_url(url)


def get_domain_name(url):
    base_url = "{0.scheme}://{0.netloc}/".format(urlsplit(url))
    return base_url
