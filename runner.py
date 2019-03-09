#from crawlers.gov_sel import SeleniumSpider
from utils.postgres_handler import DBHandler

#seleniumReviewSpider = SeleniumSpider("http://www.sova.gov.si")
#seleniumReviewSpider.check_robots()

db = DBHandler()
db.insert_site()
