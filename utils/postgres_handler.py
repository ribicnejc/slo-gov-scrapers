from postgres import Postgres
import psycopg2


class DBHandler(object):
    def __init__(self):
        self.conn = psycopg2.connect(dbname='postgres', port=5433, user='postgres', host='localhost',
                                     password='postgres1234')

    def insert_site(self):
        cursor = self.conn.cursor()
        # cursor.execute("""INSERT INTO crawldb.site
        #            (domain, robots_content, sitemap_content)
        #            VALUES ('ares.html', 'test2', 'test3');""")

        SQL = "INSERT INTO crawldb.site (domain, robots_content, sitemap_content) VALUES (%s, %s, %s);"
        values = ('ares.html', 'test2', 'test3')

        cursor.execute(SQL, values)

        self.conn.commit()

    def insert_page(self):
        pass

    def insert_image(self):
        pass

    def insert_page_data(self):
        pass

    def insert_page_type(self):
        pass

    def insert_link(self):
        pass
