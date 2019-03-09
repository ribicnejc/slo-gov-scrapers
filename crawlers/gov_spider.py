import time
import robotparser

import robotstxtparser as rps

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException


# TODO robots.txt parser

# http://www.sova.gov.si/


class SeleniumSpider(object):
    def __init__(self, url):
        self.url = url
        # sitemaps (robots.txt), shranmo slike, ce dela js,
        # htmlunit hitrejsi od seleniuma

        # http://www.pisrs.si/Pis.web/pregledPredpisa?id=ZAKO1884
        # duplikati,,, popravljanenj urlja.
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
        rp.can_fetch("*", "http://www.musi-cal.com/cgi-bin/search?city=San+Francisco")
        rp.can_fetch("*", "http://www.musi-cal.com/")

    def scrap_page(self):
        self.driver.implicitly_wait(2)
        time.sleep(1)
        review_location_name = self.driver.find_element_by_css_selector('div h1.ui_header').text
        review_location_description_tags = self.driver.find_element_by_css_selector(
            'div.headerInfoWrapper div.detail a').text
        review_current_page = self.driver.find_element_by_css_selector('div.pageNumbers a.current').get_attribute(
            'data-page-number')
        review_last_page = self.driver.find_element_by_css_selector('div.pageNumbers a.last').get_attribute(
            'data-page-number')
        place_rate = self.driver.find_element_by_css_selector('span.overallRating').text

        reviews = []
        for review in self.driver.find_elements_by_css_selector("div.review-container"):
            review_id = review.get_attribute("data-reviewid")
            user_id = review.find_element_by_css_selector('div.member_info div.memberOverlayLink').get_attribute('id')
            review_date = review.find_element_by_css_selector('span.ratingDate').get_attribute('title')
            review_rate = review.find_element_by_css_selector('span.ui_bubble_rating').get_attribute('class')
            username = review.find_element_by_css_selector('div.info_text div').text

        self.save_to_file(reviews, review_location_name, review_current_page, review_last_page)
