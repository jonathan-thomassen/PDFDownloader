'''Module providing the ResultEntry class.'''

class ResultEntry:
  def __init__(self, pdf_id):
    self.pdf_id = pdf_id
    self.results = {}

  def AddResult(self, url, result):
    self.results.update({url: result})
