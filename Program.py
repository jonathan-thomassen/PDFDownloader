import requests
import csv
import datetime
import sys
import shutil
import pathlib

from requests.exceptions import ConnectionError, RetryError
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime
from ssl import SSLCertVerificationError

argument = ''
if (len(sys.argv) > 1):
    argument = sys.argv[1]

urlDict = {}
resultList = []
resultsCsvName = 'Results_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'

if (argument == '-r'):
    print('Reset requested. Deleting all files in PDFs folder...')
    shutil.rmtree("./PDFs/")
    pathlib.Path.mkdir("PDFs")

with open("GRI_2017_2020.csv", newline="", errors="ignore") as csvFile:
    csvReader = csv.DictReader(csvFile, delimiter=",")
    id = 1
    for row in csvReader:
        urlDict.update({id: {row['pdf_url_1'], row['pdf_url_2']}})
        id += 1

session = requests.Session()
# retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[ 500, 502, 503, 504 ])
# session.mount('http://', HTTPAdapter(max_retries=retries))
# session.mount('https://', HTTPAdapter(max_retries=retries))

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

for row in urlDict:
    resultList.append([row])
    for url in urlDict[row]:
        if (url.upper().startswith('HTTP') and (url.upper().endswith('.PDF'))):
            localFilename = str(row) + '_' + url.split('/')[-1]
            try:
                # Acquire response from server
                response = session.get(url)
            except (ConnectionError, RetryError):
                print('The following file could not be downloaded (connection error): ' + url)
                resultList[row-1] += [url, 'Error: File could not be downloaded (connection error).']
                pass
            else:
                try:
                    print(response.headers['Content-Type'])
                except KeyError:
                    print('Response from server does not contain a \'Content-Type\' field: ' + url)
                    resultList[row-1] += [url, 'Error: Response from server does not contain a \'Content-Type\' field.']
                    pass
                else:
                    if (response.headers['Content-Type'] == 'application/pdf'):
                        try:
                            # Write to PDF file
                            with open('./PDFs/' + localFilename, 'xb') as f:
                                f.write(response.content)
                        except FileExistsError:
                            print('File already exists: ' + localFilename)
                            resultList[row-1] += [url, 'Error: File already exists.']
                            break
                        else:
                            print('File successfully downloaded: ' + url)
                            resultList[row-1] += [url, 'File successfully downloaded.']
                            break
                    else:
                        print('File linked to in URL is not a PDF document: ' + url)
                        resultList[row-1] += [url, 'Error: File linked to in URL is not a PDF document.']
        else:
            print('Hyperlink not a valid URL to a PDF document: ', end='')
            if (url != ''):
                print(url)
                resultList[row-1] += [url, 'Error: Hyperlink not a valid URL to a PDF document.']
            else:
                print('(blank)')
                resultList[row-1] += [url, 'Error: URL blank.']
    writeResultsCsv()