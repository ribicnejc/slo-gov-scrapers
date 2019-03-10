from managers import frontier_manager
from managers import spiders_manager

# Here we fill our frontier with first few seeds
frontier_manager.plant_seeds()

# Start crawl by releasing spiders
spiders_manager.release_spiders()
