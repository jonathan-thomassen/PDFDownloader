class UrlEntry:
    def __init__(self, id):
        self.id = id
        self.urls = []

    def AddUrl(self, url):
        self.urls.append(url)