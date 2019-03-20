from crawlers.gov_spider import SeleniumSpider
from utils import settings
from managers import frontier_manager
from threading import Thread


def spider_thread(frontier):
    spider = SeleniumSpider()
    spider.change_url(frontier.get_next())


def release_spiders():
    for e in range(settings.NUMBER_OF_SPIDERS):
        t = Thread(target=spider_thread, args=(frontier_manager,))
        t.start()
