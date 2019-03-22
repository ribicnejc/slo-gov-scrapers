import time
import re
import urllib
import requests

# from urllib.robotparser import RobotFileParser
from managers.robotparser import RobotFileParser
from urllib.robotparser import RobotFileParser
from collections import defaultdict

import selenium
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
from utils.url_helper import get_domain_name

from time import sleep

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
    def __init__(self):
        self.sitemaps = set()
        self.disallowed_urls = set()
        self.crawl_delay = 1

        self.robots_content = ""
        self.sitemap_content = ""
        self.parent = ""

        self.NUMBER_OF_RETRIES = 3
        self.retriesMap = defaultdict(int)  # saves timeout-ed pages to frontier again for NUMBER_OF_RETRIES tries

        self.db_data = DBHandler()

        self.bin_manager = binary_data_manager.Binary_manager()

        chrome_options = Options()

        chrome_options.add_argument('--ignore-certificate-errors')

        if settings.HEADLESS_BROWSER:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("User-Agent=*")
        service_args = ['--verbose']
        driver = webdriver.Chrome(
            chrome_options=chrome_options,
            service_args=service_args)
        driver.set_page_load_timeout(10)
        driver.implicitly_wait(10)
        chrome_options.add_argument('--ignore-certificate-errors')
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5)

    def check_robots(self, site_id):
        rp = RobotFileParser()
        rp.set_url(self.driver.current_url + "robots.txt")
        rp.read()
        # self.crawl_delay = rp.crawl_delay('*')

        r = requests.get(self.driver.current_url + "robots.txt")
        if r.status_code == 404:
            return
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
                self.save_link(url=elt.text, parent_url=self.url)  # creating reference as core to sitemaps
                frontier_manager.add_url(self.driver.current_url, elt.text)

    def scrap_page(self):
        print("Scraping page: " + self.driver.current_url)

        # 0 saving site
        self.save_site(self.driver.current_url)  # here is current saved domain

        site_id = self.db_data.get_site_id(get_domain_name(self.url))

        # 1 check robots
        print("Checking robots")
        self.check_robots(site_id)  # robots save sitemaps to frontier in db

        print("Updating site with sitemap content")
        self.save_site(self.driver.current_url)  # here is current saved domain

        # 2 insert current page
        print("Inserting current page")
        self.insert_page(False, self.url, site_id)

        print("Reseting bin_manager")
        self.bin_manager.reset()  # inserts take place in link searches...

        # 3 fetch all urls
        print("Searching for urls...")
        urls = self.find_links(self.driver.page_source,
                               self.driver.current_url)  # !!!!!! list of urls? # method should not save it to frontier... we should save it here first
        print("Number of urls found: " + len(urls).__str__())

        # 4 put urls to frontier
        print("Putting urls to frontier")
        for url in urls:
            if not frontier_manager.frontier.is_disallowed_url(url):
                self.insert_page(True, url, site_id)
                self.save_link(url=url, parent_url=self.url)
                # print("Inserting page, making link with: " + self.url + " -> " + url)
                frontier_manager.add_url(self.driver.current_url, url)

        # 6 fetch images
        print("Searching for images...")
        self.find_images(self.driver.page_source, self.driver.current_url)

        # 7 fetch binary files (pdf, ppts, docx,...)

        self.download_images(self.bin_manager.get_image_links())
        self.download_documents(self.bin_manager.get_document_links())
        # shrani images v pb tle

        # 8 get next url from frontier and repeat process
        print("Changing url...")
        if frontier_manager.is_not_empty():
            self.change_url(frontier_manager.get_next())
        else:
            self.driver.close()

    def change_url(self, url):
        self.sitemaps = set()
        self.sitemap_content = ""
        print("##########################################################")
        print("New url: " + url.url)
        time.sleep(settings.TIME_BETWEEN_REQUESTS)
        # self.parent = self.url
        self.url = url.url
        try:
            self.driver.get(self.url)
        except selenium.common.exceptions.TimeoutException:
            print("Timeout!!")

            if self.retriesMap[self.url] == 0:
                self.retriesMap = defaultdict(int)  # cleansing dict, we don't need past urls in our dict
            self.retriesMap[self.url] += 1
            sleep(5)  # TODO check why it timeouts
            print("Changing url...")
            if self.retriesMap[self.url] < self.NUMBER_OF_RETRIES:
                print("Retrying " + self.url + "... " + str(self.retriesMap[self.url]) + ". time")
                self.change_url(url)
            elif frontier_manager.is_not_empty():
                self.change_url(frontier_manager.get_next())
            else:
                self.driver.close()
        self.scrap_page()

    def save_site(self, url):
        domain = get_domain_name(url)
        print("Saving site: " + domain)
        robots_content = self.robots_content
        sitemap_content = self.sitemap_content
        if not self.db_data.get_site_id(domain):
            self.db_data.insert_site(domain, robots_content, sitemap_content)
        else:
            self.db_data.update_site(domain, robots_content, sitemap_content)

    def insert_page(self, frontier, url, site_id):
        # TODO duplicate???
        page_type_code = ""
        if frontier:
            page_type_code = 'FRONTIER'
            # TODO here also insert link...
            self.db_data.insert_page(site_id, page_type_code, url, None, None)
            return

        r = requests.head(url, verify=False)
        content_type = r.headers['content-type']
        if 'html' in content_type:
            page_type_code = 'HTML'

        if 'application' in content_type:
            page_type_code = 'BINARY'

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
        if not to_page:
            a = 4

            # TODO save link should be called when inserting to frontier....
            # because url = sova, and parent url is arso.. just because queue and not real parenting
        self.db_data.insert_link(from_page, to_page)

    def find_links(self, page_bd, current_curl):  # vrni vse frontier urlje, pa shrani image v bazo...
        urllist = []

        page_id = self.db_data.get_page_id(current_curl)

        page_body = BeautifulSoup(page_bd, 'html.parser')

        for link in page_body.findAll('', attrs={'href': re.compile("^https?://")}):

            # print urlparse.urlparse(link.get('href'))
            urlfetched = urllib.parse.urlparse(link.get('href')).geturl()

            docext = self.endswithWhich(urlfetched, extensions)

            if docext is None:
                frontier_manager.add_url(self.parent, urlfetched)
                urllist.append(urlfetched)
            else:
                if docext in documents_with_data:
                    # self.download_document(urlfetched, docext)
                    self.bin_manager.insert_document(
                        (urlfetched, page_id, docext))
                elif docext in imgexts:
                    self.bin_manager.insert_image(
                        (urlfetched, page_id, docext))

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
                        if docext is None:  # if it not has an extension
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

    def download_documents(self, document_links):
        for inp in document_links:
            filename, ext = self.get_file_name_from_url_and_ext(inp[0])
            self.download_document(inp[0], inp[1], ext)

    def get_file_name_from_url_and_ext(self, url):
        return self.merge_text_and_seperate_extension(str(url).split("/")[-1].split("."))

    def merge_text_and_seperate_extension(self, splited):
        text = ""
        for i in splited[:-1]:
            text += str(i)
        return text, splited[-1]

    def download_image(self, url, page_id, filename, content_type):
        try:
            data = download_helper.download(url)
        except Exception as e:
            print("Can't download image (" + str(e) + ")")
            return

        self.db_data.insert_image(page_id, filename, str(content_type).upper(),
                                  data)  # TODO pass page_id to store properly
        return

    def download_document(self, url, page_id, extension):
        try:
            data = download_helper.download(url)
        except Exception as e:
            print("Can't download document (" + str(e) + ")")
            return

        self.db_data.insert_page_data(page_id, str(extension).upper(), data)  # TODO pass page_id to store properly
        return
