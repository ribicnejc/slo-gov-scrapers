import time
from bs4 import BeautifulSoup
import re
import urllib

from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from managers import frontier_manager
from utils import settings
from utils.postgres_handler import DBHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException


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
        # chrome_options.add_argument("--headless")
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
        # 5 read binary images or content
        # print (self.driver.page_source)


        self.find_links(self.driver.page_source)

        # 6 get next url from frontier and repeat process
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

        extensions = (".js, .pdf, .jpg, .png, .ppt, .pptx")
        page = BeautifulSoup(self.driver.page_source)

        print(page.findAll('script'))

        for link in page.findAll('', attrs={'href': re.compile("^https?://")}):


            # print urlparse.urlparse(link.get('href'))
            urlfetched = str(urllib.parse.urlparse(link.get('href')))
            if(not urlfetched.endswith(extensions)):
                frontier_manager.add_url(urlfetched)
                print (link.get('href'))
            else:
                print("NOT ADDED!!!!!!!!!!!!!!!!!!!     " + urlfetched)




        #print frontier_manager.frontier.frontier

        for script in page.findAll('script'):

            for line in str(script).split("\n"):
                if(len(re.split("^https?://", line))>1):
                    print(line)
                    if (not self.parse_local(line).endswith(extensions)):
                        frontier_manager.add_url(urlfetched)
                        print(link.get('href'))




        #print frontier_manager.frontier.frontier

    def parse_local(self, s):
        # parse link out of the line containing link...
        return "NOT IMPLEMENTED"