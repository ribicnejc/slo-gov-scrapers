import time
from bs4 import BeautifulSoup
import re
import urllib

from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from managers import frontier_manager
from utils import settings
from utils import download_helper
from utils.postgres_handler import DBHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException

documents_with_data = (".DOC", ".DOCX", ".PDF", ".PPT", ".PPTX.")
jpg = (".JPG", ".PNG", ".TIFF")  # TODO fill
extensions = documents_with_data + jpg


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
        # pass
        rp = RobotFileParser()

        self.url = "https://www.tripadvisor.com/"

        rp.set_url(self.url + "robots.txt")
        rp.read()
        self.robots_content = rp.__str__()
        self.crawl_delay = rp.crawl_delay('*')
        # todo check for excluded sites

    # @stale_decorator
    def scrap_page(self):
        # 1 check robots
        self.check_robots()

        # 2 save site
        self.save_site()

        # 3 fetch all urls
        # 4 put urls to frontier
        self.find_links(self.driver.page_source)

        # 5 fetch images

        # 6 fetch binary files (pdf, ppts, docx,...)

        # 7 get next url from frontier and repeat process
        if frontier_manager.is_not_empty():
            self.change_url(frontier_manager.get_next())
        else:
            self.driver.close()

    def change_url(self, url):
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

        page = BeautifulSoup(self.driver.page_source)

        print(page.findAll('script'))

        for link in page.findAll('', attrs={'href': re.compile("^https?://")}):

            # print urlparse.urlparse(link.get('href'))
            urlfetched = urllib.parse.urlparse(link.get('href')).geturl()
            if (not urlfetched.endswith(extensions)):
                frontier_manager.add_url(urlfetched)
                print(urlfetched)
            else:
                print("NOT ADDED!!!!!!!!!!!!!!!!!!!     " + urlfetched)

        # print frontier_manager.frontier.frontier

        for script in page.findAll('script'):

            for line in str(script).split("\n"):
                # parsin urls from line
                urls_parsed_from_line = re.findall(
                    'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line);

                if (len(urls_parsed_from_line) > 0):
                    for i in urls_parsed_from_line:
                        urlfetched = urllib.parse.urlparse(i)
                        # if pictures need to be downloaded, replace extensions instead of documents_with_data
                        extension = self.endswithWhich(urlfetched, documents_with_data)
                        if not extension:  # if it not has an extension
                            frontier_manager.add_url(urlfetched.geturl())
                        else:
                            self.download_document(urlfetched, extension)

                            # print frontier_manager.frontier.frontier

    def endswithany(self, s, exts):
        for i in exts:
            if str(s).endswith(i):
                return True
        return False

    def endswithWhich(self, s, exts):
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
