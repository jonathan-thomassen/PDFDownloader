class ResultEntry:
    def __init__(self, id):
        self.id = id
        self.results = {}

    def AddResult(self, url, result):
        self.results.update({url: result})