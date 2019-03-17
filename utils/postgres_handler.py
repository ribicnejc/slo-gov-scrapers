from postgres import Postgres
import psycopg2


class DBHandler(object):
    def __init__(self):
        self.conn = psycopg2.connect(dbname='postgres', port=5433, user='postgres', host='localhost',
                                     password='postgres1234')

    def insert_site(self, domain, robots_content, sitemap_content):
        cursor = self.conn.cursor()
        # cursor.execute("""INSERT INTO crawldb.site
        #            (domain, robots_content, sitemap_content)
        #            VALUES ('ares.html', 'test2', 'test3');""")

        SQL = "INSERT INTO crawldb.site (domain, robots_content, sitemap_content) VALUES (%s, %s, %s);"
        values = (domain, robots_content, sitemap_content)
        cursor.execute(SQL, values)
        self.conn.commit()

    def insert_page(self, site_id, page_type_code, url, html_content, http_status_code):
        cursor = self.conn.cursor()
        SQL = "INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) VALUES (%s, %s, %s, %s, %s, %s);"
        values = (site_id, page_type_code, url, html_content, http_status_code, "now")
        cursor.execute(SQL, values)
        self.conn.commit()

    def insert_image(self, page_id, filename, content_type, data):
        cursor = self.conn.cursor()
        SQL = "INSERT INTO crawldb.image (page_id, filename, content_type, data, accessed_time) VALUES (%s, %s, %s, %s, %s)"
        values = (page_id, filename, content_type, data, "now")
        cursor.execute(SQL, values)
        self.conn.commit()

    def insert_page_data(self, page_id, data_type_code, data):
        cursor = self.conn.cursor()
        binary = psycopg2.Binary(data)  # binary read is implemented in download, fix if bad practice

        SQL = "INSERT INTO crawldb.page_data (page_id, data_type_code, data) VALUES (%s, %s, %s);"
        values = (page_id, data_type_code, binary)
        cursor.execute(SQL, values)

        self.conn.commit()

    def insert_page_data_string(self, page_id, data_type_code, datastring):
        cursor = self.conn.cursor()
        SQL = "INSERT INTO crawldb.page_data (page_id, data_type_code, data) VALUES (%s, %s, %s);"
        values = (page_id, data_type_code, datastring)
        cursor.execute(SQL, values)
        self.conn.commit()

    def insert_page_type(self, code):
        cursor = self.conn.cursor()
        SQL = "INSERT INTO crawldb.page_type (code) VALUES (%s);"
        values = (code,)
        cursor.execute(SQL, values)
        self.conn.commit()

    def insert_link(self, from_page, to_page):
        cursor = self.conn.cursor()
        SQL = "INSERT INTO crawldb.link (from_page, to_page) VALUES (%s, %s);"
        values = (from_page, to_page)
        cursor.execute(SQL, values)
        self.conn.commit()

    def get_site_id(self, url_domain_name):
        cursor = self.conn.cursor()
        SQL = """SELECT id
	             FROM crawldb.site
	             WHERE domain=%s;"""
        values = (url_domain_name,)
        cursor.execute(SQL, values)
        s = cursor.fetchone()
        if s != None:
            return s[0]
        else:
            return None

    def get_page_id(self, url):
        cursor = self.conn.cursor()
        SQL = """SELECT id
                 FROM crawldb.page
                 WHERE url=%s;"""
        values = (url,)
        cursor.execute(SQL, values)
        return cursor.fetchone()[0]
