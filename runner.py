from crawlers.gov_sel import SeleniumSpider

seleniumReviewSpider = SeleniumSpider("http://evem.gov.si/evem/drzavljani/zacetna.evem")
seleniumReviewSpider.scrap_page()