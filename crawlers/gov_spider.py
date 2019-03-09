import time
import robotparser
import robotstxtparser as rps
from bs4 import BeautifulSoup
import re


from managers import frontier_manager
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
        chrome_options = Options()
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
        rp = robotparser.RobotFileParser()
        rp.set_url(self.url + "/robots.txt")
        rp.read()
        #todo

    def scrap_page(self):
        self.driver.implicitly_wait(2)
        time.sleep(1)
        print self.driver.page_source

        # page = BeautifulSoup(self.driver.page_source)

        # print page
        # review_location_name = self.driver.find_element_by_css_selector('div h1.ui_header').text


    def find_links(self, page):
        page = BeautifulSoup(self.driver.page_source)

        for link in page.findAll('a', attrs={'href': re.compile("^http://")}):
            print link.get('href')

