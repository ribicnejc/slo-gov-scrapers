import time
import re
import urllib
import requests

from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from managers import frontier_manager
from managers import binary_data_manager
from managers.frontier_manager import ScrapUrl
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
        self.url = url.url
        self.sitemaps = set()
        self.disallowed_urls = set()
        self.crawl_delay = 1

        self.robots_content = ""
        self.parent = url.parent
        self.sitemap_content = ""

        self.db_data = DBHandler()

        self.bin_manager = binary_data_manager.Binary_manager()

        chrome_options = Options()
        if settings.HEADLESS_BROWSER:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("User-Agent=*")
        service_args = ['--verbose']
        driver = webdriver.Chrome(
            chrome_options=chrome_options,
            service_args=service_args)
        driver.get(self.url)
        driver.implicitly_wait(2)
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5)

    def check_robots(self, site_id):
        rp = RobotFileParser()
        rp.set_url(self.url + "robots.txt")
        rp.read()
        self.crawl_delay = rp.crawl_delay('*')
        r = requests.get(self.url + "robots.txt")
        content = r.content.decode('utf-8').split('\n')
        self.robots_content = content
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
            self.sitemap_content = self.sitemap_content + "," + r.content.decode('utf-8')
            e = BeautifulSoup(r.content, 'html.parser')
            for elt in e.find_all('loc'):
                self.insert_page(True, elt.text, site_id)
                frontier_manager.add_url(self.driver.current_url, elt.text)

    def scrap_page(self):
        # 1 check robots

        site_id = self.db_data.get_site_id(self.get_domain_name(self.url))

        self.check_robots(site_id)  # robots save sitemaps to frontier in db

        # 2 save site
        self.save_site(self.driver.current_url)  # here is current saved domain

        self.bin_manager.reset()  # inserts take place in link searches...

        # 3 fetch all urls
        urls = self.find_links(self.driver.page_source,
                               self.driver.current_url)  # !!!!!! list of urls? # method should not save it to frontier... we should save it here first

        # 4 put urls to frontier
        for url in urls:
            if not frontier_manager.frontier.is_disallowed_url(url):
                self.insert_page(True, url, site_id)
                frontier_manager.add_url(self.driver.current_url, url)

        # 5 make connection to parent url
        self.save_link(self.url, self.parent)

        # 6 fetch images
        self.find_images(self.driver.page_source, self.driver.current_url)

        # 7 fetch binary files (pdf, ppts, docx,...)
        # shrani images v pb tle

        # 8 get next url from frontier and repeat process
        if frontier_manager.is_not_empty():
            self.change_url(frontier_manager.get_next())
        else:
            self.driver.close()

    def change_url(self, url):
        self.sitemaps = set()
        self.sitemap_content = ""
        time.sleep(settings.TIME_BETWEEN_REQUESTS)
        self.parent = self.url
        self.url = url.url
        self.driver.get(url)
        self.scrap_page()

    def save_site(self, url):
        domain = self.get_domain_name(url)
        print("Saving site: " + domain)
        robots_content = self.robots_content
        sitemap_content = self.driver.page_source
        self.db_data.insert_site(domain, robots_content, sitemap_content)

    def insert_page(self, frontier, url, site_id):
        # TODO duplicate???
        page_type_code = ""
        if frontier:
            page_type_code = 'FRONTIER'
            self.db_data.insert_page(site_id, page_type_code, url, None, None)
            return

        r = requests.head(url)
        content_type = r.headers['content-type']
        if 'html' in content_type:
            page_type_code = 'HTML'

        if 'application' in content_type:
            page_type_code = 'BINARY'
        if 300 < r.status_code < 310:
            page_type_code = "303"

        url = r.url
        html_content = self.driver.page_source
        if 'HTML' not in page_type_code:
            html_content = None

        http_status_code = r.status_code
        self.db_data.insert_page(site_id, page_type_code, url, html_content, http_status_code)

    def save_link(self, url, parent_url):
        if parent_url:
            from_page = self.db_data.get_page_id(parent_url)  # get parent id
        else:  # seed url
            from_page = self.db_data.get_page_id(url)
        to_page = self.db_data.get_page_id(url)  # get current id
        self.db_data.insert_link(from_page, to_page)

    @staticmethod
    def get_domain_name(url):
        return url.split('//')[-1].split('/')[0]

    def find_links(self, page_bd, current_curl):  # vrni vse frontier urlje, pa shrani image v bazo...

        urllist = []

        page_id = self.db_data.get_page_id(current_curl)

        page_body = BeautifulSoup(page_bd)

        print(page_body.findAll('script'))

        for link in page_body.findAll('', attrs={'href': re.compile("^https?://")}):

            # print urlparse.urlparse(link.get('href'))
            urlfetched = urllib.parse.urlparse(link.get('href')).geturl()

            docext = self.endswithWhich(urlfetched, extensions)

            if (not docext):
                frontier_manager.add_url(self.parent, urlfetched)
                urllist.append(urlfetched)
                print(urlfetched)
            else:
                if docext in documents_with_data:
                    # self.download_document(urlfetched, docext)
                    self.bin_manager.insert_document(
                        (urlfetched, page_id, docext))  # TODO insert also pageId and other data
                elif docext in imgexts:
                    self.bin_manager.insert_image(
                        (urlfetched, page_id, docext))  # TODO insert also pageId and other data

        # print frontier_manager.frontier.frontier

        for script in page_body.findAll('script'):

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
                            frontier_manager.add_url(self.parent, urlfetched)  # URLs for frontier...
                            urllist.append(urlfetched)
                        else:
                            if docext in documents_with_data:
                                # self.download_document(urlfetched, docext)
                                # ( url, page id, extension)
                                self.bin_manager.insert_document(
                                    (urlfetched, page_id, docext))  # TODO insert also pageId and other data
                            elif docext in imgexts:
                                self.bin_manager.insert_image(
                                    (urlfetched, page_id, docext))  # TODO insert also pageId and other data

                                # print frontier_manager.frontier.frontier

        return urllist

    def find_images(self, page, current_curl):

        page_id = self.db_data.get_page_id(current_curl)

        page = BeautifulSoup(self.driver.page_source, 'html.parser')

        images = []
        for img_url in page.findAll('img'):
            images.append(img_url.get('src'))
            # self.bin_manager.insert_image((img_url, page_id, self.endswithWhich(img_url)))

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

    def queryless_url(self, url):
        if "?" in url:
            index = url.find("?")
            return url[:index]

        return url

    def download_images(self, image_links):
        for inp in image_links:
            filename, ext = self.get_file_name_from_url_and_ext(inp[0])
            self.download_image(inp[0], inp[1], filename, ext)

    def get_file_name_from_url_and_ext(self, url):
        return self.merge_text_and_seperate_extension(str(url).split("/")[-1].split("."))

    def merge_text_and_seperate_extension(self, splited):
        text = ""
        for i in splited[:-1]:
            text += str(i)
        return text, splited[-1]


@staticmethod
def download_image(url, page_id, filename, content_type):
    data = download_helper.download(url)

    DBHandler.insert_image(page_id, filename, content_type, data)  # TODO pass page_id to store properly
    return


@staticmethod
def download_document(url, page_id, extension):
    data = download_helper.download(url)
    DBHandler.insert_page_data(page_id, extension, data)  # TODO pass page_id to store properly
    return
