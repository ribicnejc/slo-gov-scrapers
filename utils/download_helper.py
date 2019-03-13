import urllib.request


def download(url):
    response = urllib.request.urlopen(url)
    data = response.read()      # a `bytes` object
    return data


def download_encoded_text(url, enc=""):
    response = urllib.request.urlopen(url)
    data = response.read()  # a `bytes` object
    text = data.decode(enc)

    return text
