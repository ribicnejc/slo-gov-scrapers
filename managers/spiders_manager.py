from crawlers.gov_spider import SeleniumSpider
from utils import settings
from managers import frontier_manager
from threading import Thread


def spider_thread(frontier):
    spider = SeleniumSpider(frontier.get_next())
    spider.scrap_page()


def release_spiders():
    for e in range(settings.NUMBER_OF_SPIDERS):
        t = Thread(target=spider_thread, args=(frontier_manager,))
        t.start()
