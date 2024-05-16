'''Module providing the UrlEntry class.'''

class UrlEntry:
  def __init__(self, pdf_id):
    self.pdf_id = pdf_id
    self.urls = []

  def AddUrl(self, url):
    self.urls.append(url)
