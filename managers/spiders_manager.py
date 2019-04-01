from crawlers.gov_spider import SeleniumSpider
from utils import settings
from managers import frontier_manager
from threading import Thread


def spider_thread(frontier, e):
    spider = SeleniumSpider(e)
    spider.crawl()


def release_spiders():
    frontier_manager.init_thread_stop_flags()
    for e in range(settings.NUMBER_OF_SPIDERS):
        t = Thread(target=spider_thread, args=(frontier_manager, e))
        t.start()
