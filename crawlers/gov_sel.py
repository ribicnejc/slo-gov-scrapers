import time

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
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        service_args = ['--verbose']
        driver = webdriver.Chrome(
            chrome_options=chrome_options,
            service_args=service_args)
        driver.get(url)
        driver.implicitly_wait(2)
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5)

    @stale_decorator
    def select_all_languages(self):
        time.sleep(1)
        all_languages = self.driver.find_element_by_xpath('//div[@data-value="ALL"]')
        all_languages.click()
        time.sleep(1)
        self.driver.implicitly_wait(2)

    @stale_decorator
    def is_all_languages_selected(self):
        all_languages = self.driver.find_element_by_xpath('//input[@id="filters_detail_language_filterLang_ALL"]')
        return all_languages.is_selected()

    @stale_decorator
    def has_next_review_page(self):
        return not (self.get_next_page_url() is None)

    @stale_decorator
    def get_next_page_url(self):
        next_url = self.driver.find_element_by_css_selector('div.ui_pagination a.next').get_attribute("href")
        return next_url

    @stale_decorator
    def get_coordinates(self):
        coord_url = self.driver.find_element_by_css_selector("div.staticMap img").get_attribute("src")
        return coord_url

    @stale_decorator
    def next_page(self):
        try:
            if not self.is_all_languages_selected():
                self.select_all_languages()
            self.driver.find_element_by_css_selector('div.ui_pagination a.next').click()
        except WebDriverException:
            self.driver.implicitly_wait(2)

    @stale_decorator
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

    def refresh_page(self):
        self.driver.refresh()

    def stop_spider(self):
        self.driver.close()

    @staticmethod
    def save_to_file(reviews, location_name, current_page, last_page):
        filename = 'data/data_reviews/selenium_reviews-%s-%s-%s.csv' % (location_name, current_page, last_page)
