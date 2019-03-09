from postgres import Postgres


class DBHandler(object):
    def __init__(self):
        self.db = Postgres("postgres://postgres@localhost/postgres")

    def insert_site(self):
        pass

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
