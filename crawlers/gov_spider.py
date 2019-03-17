import time
import re
import urllib
import requests

from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from xml.etree import ElementTree
from managers import frontier_manager
from utils import settings
from utils import download_helper
from utils.postgres_handler import DBHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException

miscexts = (".js", ".css")
documents_with_data = (".DOC", ".DOCX", ".PDF", ".PPT", ".PPTX.", ".doc", ".docx", ".pdf", ".ppt", ".pptx.")
imgexts = (".JPG", ".PNG", ".TIFF", ".GIF", ".jpg", ".png", ".tiff", ".gif")  # TODO fill
extensions = documents_with_data + imgexts + miscexts


def stale_decorator(f):
    def wrapper(*args, **kwargs):
        counter = 10
        while counter != 0:
            try:
                result = f(*args, **kwargs)
                return result
            except StaleElementReferenceException:
                counter -= 1
            except WebDriverException:
                counter -= 1
        return None

    return wrapper


class SeleniumSpider(object):
    def __init__(self, url):
        self.url = url
        self.sitemaps = set()
        self.disallowed_urls = set()
        self.crawl_delay = 1
        self.robots_content = ""
        # self.db_data = DBHandler()
        chrome_options = Options()
        if settings.HEADLESS_BROWSER:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("User-Agent=*")
        service_args = ['--verbose']
        driver = webdriver.Chrome(
            chrome_options=chrome_options,
            service_args=service_args)
        driver.get(url)
        driver.implicitly_wait(2)
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5)

    def check_robots(self):
        rp = RobotFileParser()
        rp.set_url(self.url + "robots.txt")
        rp.read()
        self.robots_content = rp.__str__()
        self.crawl_delay = rp.crawl_delay('*')
        r = requests.get(self.url + "robots.txt")
        content = r.content.decode('utf-8').split('\n')
        for el in content:
            if 'Sitemap' in el:
                self.sitemaps.add(el.replace('Sitemap: ', ''))

        if rp.default_entry is not None:
            if rp.default_entry.rulelines is not None:
                for rule in rp.default_entry.rulelines:
                    if rule and not rule.allowance:
                        frontier_manager.add_disallowed_url(self.url[0:-1] + rule.path)

        for sitemap in self.sitemaps:
            r = requests.get(sitemap)
            e = BeautifulSoup(r.content)
            for elt in e.find_all('loc'):
                frontier_manager.add_url(elt.text)

    # @stale_decorator
    def scrap_page(self):
        # 1 check robots
        self.check_robots()

        # 2 save site
        self.save_site()

        # 3 fetch all urls
        # 4 put urls to frontier

        imageLinks = self.find_links(self.driver.page_source)

        # 5 fetch images
        self.find_images(self.driver.page_source)

        # 6 fetch binary files (pdf, ppts, docx,...)

        # 7 get next url from frontier and repeat process
        if frontier_manager.is_not_empty():
            self.change_url(frontier_manager.get_next())
        else:
            self.driver.close()

    def change_url(self, url):
        self.sitemaps = set()
        self.sitemaps = set()
        time.sleep(settings.TIME_BETWEEN_REQUESTS)
        self.driver.get(url)
        self.scrap_page()

    def save_site(self):
        return
        # todo domain name etc...
        domain = self.driver.current_url
        robots_content = self.robots_content
        sitemap_content = self.driver.page_source
        self.db_data.insert_site(domain, robots_content, sitemap_content)

    def insert_page(self):
        site_id = self.db_data.get_site_id(self.driver.current_url)

    def find_links(self, page):

        imageUrls = []

        page = BeautifulSoup(self.driver.page_source)

        print(page.findAll('script'))

        for link in page.findAll('', attrs={'href': re.compile("^https?://")}):

            # print urlparse.urlparse(link.get('href'))
            urlfetched = urllib.parse.urlparse(link.get('href')).geturl()

            docext = self.endswithWhich(urlfetched, extensions)

            if (not docext):
                frontier_manager.add_url(urlfetched)
                print(urlfetched)
            else:
                if docext in documents_with_data:
                    self.download_document(urlfetched, docext)
                elif docext in imgexts:
                    imageUrls.append(urlfetched)

        # print frontier_manager.frontier.frontier

        for script in page.findAll('script'):

            for line in str(script).split("\n"):
                # parsin urls from line
                urls_parsed_from_line = re.findall(
                    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line);

                if (len(urls_parsed_from_line) > 0):
                    for i in urls_parsed_from_line:
                        urlfetched = urllib.parse.urlparse(i).geturl()
                        # if pictures need to be downloaded, replace extensions instead of documents_with_data
                        docext = self.endswithWhich(urlfetched, extensions)
                        if not docext:  # if it not has an extension
                            frontier_manager.add_url(urlfetched)
                        else:
                            if docext in documents_with_data:
                                self.download_document(urlfetched, docext)
                            elif docext in imgexts:
                                imageUrls.append(urlfetched)

                                # print frontier_manager.frontier.frontier

        return imageUrls

    def find_images(self, page):

        page = BeautifulSoup(self.driver.page_source)

        images = []
        for img in page.findAll('img'):
            images.append(img.get('src'))

        print(images)

    def endswithany(self, s, exts):
        if "?" in s:
            index = s.find("?")
            s = s[:index]

        for i in exts:
            if str(s).endswith(i):
                return True
        return False

    def endswithWhich(self, s, exts):
        if "?" in s:
            index = s.find("?")
            s = s[:index]

        for i in exts:
            if str(s).endswith(i):
                return i
        return None

    def download_image(self, url, page_id, filename, content_type):
        data = download_helper.download(url)
        DBHandler.insert_image(page_id, filename, content_type, data)  # TODO pass page_id to store properly
        return

    def download_document(self, url, page_id, extension):
        data = download_helper.download(url)
        DBHandler.insert_page_data(page_id, extension, data)  # TODO pass page_id to store properly
        return
