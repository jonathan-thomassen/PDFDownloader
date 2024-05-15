import requests
import csv
import datetime
import sys

from requests.exceptions import ConnectionError, RetryError
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime
from ssl import SSLCertVerificationError
from pathlib import Path
from UrlEntry import UrlEntry
from ResultEntry import ResultEntry

# Currently missing: 69
# TODO: Lav klasser af listerne. 

urlListCsvPath = './GRI_2017_2020.csv'
pdfWriterArg = 'xb'
overwrite = False

urlList = []
resultList = []

resultsCsvName = 'Results_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv' 
session = requests.Session()
retries = Retry(total=5, backoff_factor=0.1)
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
httpHeaders = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Cache-Control": "no-cache",
    "Dnt": "1",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

if (len(sys.argv) > 1):
    argument = sys.argv[1]
    if (argument != None and argument == '-o'):
        print('Overwrite flag set. Downloader will overwrite old files.')
        pdfWriterArg = 'wb'
        overwrite = True

def readUrlListCsv(filePath, delimiter, quotechar) :
    with open(filePath, newline="", errors="ignore") as csvFile:
        csvReader = csv.reader(csvFile, delimiter=delimiter, quotechar=quotechar)
        n = 0
        for row in csvReader:
            if (n > 0):
                urlList.append(UrlEntry(row[0]))
                for element in row[1:]:
                    urlList[-1].AddUrl(element)
            n += 1

def writeResultsCsv():
    with open(resultsCsvName, 'w', newline='') as csvFile:
        csvWriter = csv.writer(csvFile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(['Id', 'URL_1', 'Result_1', 'URL_2', 'Result_2'])
        for resultEntry in resultList:
            csvRow = []
            csvRow.append(resultEntry.id)

            for url, result in resultEntry.results.items():
                csvRow.append(url)
                csvRow.append(result)

            while (len(csvRow) < 5):
                csvRow.append('')

            csvWriter.writerow(csvRow)

def writePdfToFile(content, localFilename, url, id):
    try:
        with open('./PDFs/' + localFilename, pdfWriterArg) as f:
            f.write(content)
    except FileExistsError:
        print('Id: ' + id + '. File already exists: ' + localFilename)
        resultList[-1].AddResult(url, 'Error: File already exists.')
    else:
        print('Id: ' + id + '. File successfully downloaded: ' + url)
        resultList[-1].AddResult(url, 'File successfully downloaded.')

def doesFileExists(localFilename):
    path = Path('./PDFs/' + localFilename)
    if (path.is_file()):
        return True
    return False

def downloadPdfs():
    for row in urlList:
        resultList.append(ResultEntry(row.id))
        for url in row.urls:
            # TODO: Eventuelt lav check om til funktion
            if (url.upper().startswith('HTTP')):
                if (url.upper().startswith('HTTP:')):
                    url = 'https:' + url[5:]
                localFilename = str(row.id) + '_' + url.split('/')[-1]
                if (localFilename.upper().endswith('.PDF') == False):
                    localFilename += '.pdf'
                if (overwrite == False):
                    if (doesFileExists(localFilename)):
                        print('Id: ' + row.id + '. File already exists: ' + localFilename)
                        resultList[-1].AddResult(url, 'Error: File already exists.')
                        break
                try:
                    # Acquire response from server
                    print('Id: ' + row.id + '. Sending \'GET\' request: ' + url)
                    # TODO: Prøv at lege med timeout værdier
                    response = session.get(url, timeout=(6.05, 120), verify=False, headers=httpHeaders)
                # TODO: Læs op på session og ConnectionError
                except (ConnectionError, RetryError):
                    print('Id: ' + row.id + '. The following file could not be downloaded (connection error): ' + url)
                    resultList[-1].AddResult(url, 'Error: File could not be downloaded (connection error).')
                    pass
                else:
                    try:
                        contentType = response.headers['Content-Type']
                    except KeyError:
                        print('Id: ' + row.id + '. Response from server does not contain a \'Content-Type\' field: ' + url)
                        resultList[-1].AddResult(url, 'Error: Response from server does not contain a \'Content-Type\' field.')
                        pass
                    else:
                        if (contentType == 'application/pdf'):
                            content = response.content
                            if (sys.getsizeof(content) > 0):
                                writePdfToFile(content, localFilename, url, row.id)
                                break
                        print('Id: ' + row.id + '. File linked to in URL is not a PDF document: ' + url)
                        resultList[-1].AddResult(url, 'Error: File linked to in URL is not a PDF document.')                   
            else:
                print('Id: ' + row.id + '. Hyperlink not a valid URL to a PDF document: ', end='')
                if (url != ''):
                    print(url)
                    resultList[-1].AddResult(url, 'Error: Hyperlink not a valid URL to a PDF document.')
                else:
                    print('(blank)')
                    resultList[-1].AddResult(url, 'Error: URL blank.')
        writeResultsCsv()

readUrlListCsv(urlListCsvPath, ',', '|')
downloadPdfs()