from crawlers.gov_spider import SeleniumSpider
from utils.postgres_handler import DBHandler
from managers import frontier_manager

# import thread

# Here we fill our frontier with first few seeds
frontier_manager.plant_seeds()

spider1 = SeleniumSpider(frontier_manager.get_next())
# spider2 = SeleniumSpider(frontier_manager.get_next())
# spider3 = SeleniumSpider(frontier_manager.get_next())

# while frontier_manager.is_not_empty():

spider1.scrap_page()
# spider2.scrap_page()
# spider3.scrap_page()

db = DBHandler()
db.insert_site()

