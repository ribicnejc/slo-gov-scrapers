from crawlers.gov_selen import SeleniumSpider
from utils.postgres_handler import DBHandler

seleniumReviewSpider = SeleniumSpider("http://www.sova.gov.si")
seleniumReviewSpider.check_robots()

db = DBHandler()
db.insert_site()
