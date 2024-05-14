import requests
import csv
import datetime
import sys

from requests.exceptions import ConnectionError, RetryError
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime
from ssl import SSLCertVerificationError

argument = ''
pdfWriterArg = 'xb'

if (len(sys.argv) > 1):
    argument = sys.argv[1]
    if (argument == '-r'):
        print('Reset requested. Downloader will overwrite old files.')
        pdfWriterArg = 'wb'

urlList = []
resultList = []
resultsCsvName = 'Results_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv' 

with open("GRI_2017_2020.csv", newline="", errors="ignore") as csvFile:
    csvReader = csv.reader(csvFile, delimiter=",", quotechar="|")
    n = 0
    for row in csvReader:
        if (n > 0):
            urlList.append([row[0]])
            urlAB = []
            for element in row[1:]:
                urlAB.append(element)

            urlList[-1].append(urlAB)
        n += 1

session = requests.Session()
# retries = Retry(total=10, backoff_factor=0.1)
# session.mount('http://', HTTPAdapter(max_retries=retries))
# session.mount('https://', HTTPAdapter(max_retries=retries))

httpHeaders = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Cache-Control": "no-cache",
    "Dnt": "1",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def writeResultsCsv():
    with open(resultsCsvName, 'w', newline='') as csvFile:
        csvWriter = csv.writer(csvFile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(['Id', 'URL_1', 'Result_1', 'URL_2', 'Result_2'])
        for row in resultList:
            while (len(row) < 5):
                row.append('')

            csvRow = []
            for value in row:
                csvRow.append(value)

            csvWriter.writerow(csvRow)

def downloadPdfs():
    for row in urlList:
        resultList.append([row[0]])
        for url in row[1]:
            if (url.upper().startswith('HTTP') and (url.upper().endswith('.PDF'))):
                if (url.upper().startswith('HTTP:')):
                    url = 'https:' + url[5:]
                localFilename = str(row[0]) + '_' + url.split('/')[-1]
                try:
                    # Acquire response from server
                    response = session.get(url)
                except (ConnectionError, RetryError):
                    try:
                        # Try with headers
                        response = session.get(url, headers=httpHeaders)
                    except (ConnectionError, RetryError):   
                        print('The following file could not be downloaded (connection error): ' + url)
                        resultList[-1] += [url, 'Error: File could not be downloaded (connection error).']
                        pass
                    else:
                        try:
                            print(response.headers['Content-Type'])
                        except KeyError:
                            print('Response from server does not contain a \'Content-Type\' field: ' + url)
                            resultList[-1] += [url, 'Error: Response from server does not contain a \'Content-Type\' field.']
                            pass
                        else:
                            if (response.headers['Content-Type'] == 'application/pdf'):
                                try:
                                    # Write to PDF file
                                    with open('./PDFs/' + localFilename, pdfWriterArg) as f:
                                        f.write(response.content)
                                except FileExistsError:
                                    print('File already exists: ' + localFilename)
                                    resultList[-1] += [url, 'Error: File already exists.']
                                    break
                                else:
                                    print('File successfully downloaded: ' + url)
                                    resultList[-1] += [url, 'File successfully downloaded.']
                                    break
                            else:
                                print('File linked to in URL is not a PDF document: ' + url)
                                resultList[-1] += [url, 'Error: File linked to in URL is not a PDF document.']
                else:
                    try:
                        print(response.headers['Content-Type'])
                    except KeyError:
                        print('Response from server does not contain a \'Content-Type\' field: ' + url)
                        resultList[-1] += [url, 'Error: Response from server does not contain a \'Content-Type\' field.']
                        pass
                    else:
                        if (response.headers['Content-Type'] == 'application/pdf'):
                            try:
                                # Write to PDF file
                                with open('./PDFs/' + localFilename, pdfWriterArg) as f:
                                    f.write(response.content)
                            except FileExistsError:
                                print('File already exists: ' + localFilename)
                                resultList[-1] += [url, 'Error: File already exists.']
                                break
                            else:
                                print('File successfully downloaded: ' + url)
                                resultList[-1] += [url, 'File successfully downloaded.']
                                break
                        else:
                            print('File linked to in URL is not a PDF document: ' + url)
                            resultList[-1] += [url, 'Error: File linked to in URL is not a PDF document.']
            else:
                print('Hyperlink not a valid URL to a PDF document: ', end='')
                if (url != ''):
                    print(url)
                    resultList[-1] += [url, 'Error: Hyperlink not a valid URL to a PDF document.']
                else:
                    print('(blank)')
                    resultList[-1] += [url, 'Error: URL blank.']
        writeResultsCsv()

downloadPdfs()