from postgres import Postgres
import psycopg2


class DBHandler(object):
    def __init__(self):
        self.conn = psycopg2.connect(dbname='postgres', port=5432, user='postgres', host='localhost',
                                     # port 5433 - miha, port 5432 - nejc
                                     password='postgres')  # postgres1234 - miha, postgres - nejc

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
        SQL = """INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) 
        VALUES (%s, %s, %s, %s, %s, %s) 
        ON CONFLICT (url) DO UPDATE 
        SET page_type_code = %s,
            html_content = %s,
            http_status_code = %s,
            accessed_time = %s;"""
        values = (site_id, page_type_code, url, html_content, http_status_code, "now",
                  page_type_code, html_content, http_status_code, "now")
        cursor.execute(SQL, values)
        self.conn.commit()

    def update_site(self, domain, robots_content, sitemap_content):

        cursor = self.conn.cursor()
        SQL = """UPDATE crawldb.site
                SET robots_content=%s, sitemap_content=%s
                WHERE domain=%s;"""
        values = (robots_content, sitemap_content, domain)
        cursor.execute(SQL, values)
        self.conn.commit()

    def update_page_content(self, page_id, html_content, status_code):
        cursor = self.conn.cursor()
        SQL = """UPDATE crawldb.page
                    SET html_content=%s, http_status_code=%s, accessed_time=%s
                    WHERE id=%s;"""
        values = (html_content, status_code, "now", page_id)
        cursor.execute(SQL, values)
        self.conn.commit()

    def update_page(self):
        cursor = self.conn.cursor()
        SQL = """UPDATE crawldb.page
                SET id=?, site_id=?, page_type_code=?, url=?, html_content=?, http_status_code=?, accessed_time=?
                WHERE <condition>;"""
        values = ()
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
        SQL = """INSERT INTO crawldb.link (from_page, to_page) VALUES (%s, %s) 
        ON CONFLICT (from_page, to_page) DO UPDATE 
        SET from_page = %s,
            to_page = %s;
        """
        values = (from_page, to_page, from_page, to_page)
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
        if s is not None:
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
        s = cursor.fetchone()
        if s is not None:
            return s[0]
        else:
            return None
