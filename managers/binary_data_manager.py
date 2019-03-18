
class Binary_manager:

    def __init__(self):
        self.image_links = []
        self.document_links = []

    def insert_image(self, value):
        self.image_links.append(value)

    def insert_document(self, value):
        self.document_links.append(value)

    def get_image_links(self):
        return self.image_links

    def get_document_links(self):
        return self.document_links

    def reset_images(self):
        self.image_links = []

    def reset_documents(self):
        self.document_links = []

    def reset(self):
        self.reset_documents()
        self.reset_images()

