from w3lib import url as w3url


def url_canon(url):
    return w3url.canonicalize_url(url)


def get_domain_name(url):
        return url.split('//')[-1].split('/')[0]
