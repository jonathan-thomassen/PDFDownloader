import requests
import csv
import datetime

from requests.exceptions import ConnectionError, RetryError
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime

urlDict = {}
resultList = []
resultsCsvName = 'Results_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'

with open("GRI_2017_2020.csv", newline="", errors="ignore") as csvFile:
    csvReader = csv.DictReader(csvFile, delimiter=",")
    id = 1
    for row in csvReader:
        print(row["pdf_url_1"])
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
                response = session.get(url, verify=False)
            except (ConnectionError, RetryError) as e:
                print('The following file could not be downloaded (connection error): ' + url)
                resultList[row-1] += [url, 'Error: File could not be downloaded (connection error).']
                pass
            else:
                print(response.headers['Content-Type'])
                if (response.headers['Content-Type'] == 'application/pdf'):
                    try:
                        # Write to PDF file
                        with open('./PDFs/' + localFilename, 'xb') as f:
                            f.write(response.content)
                        print('Successfully downloaded: ' + url)
                        resultList[row-1] += [url, 'Succesfully downloaded.']
                        break
                    except FileExistsError:
                        print('File already exists: ' + localFilename)
                        resultList[row-1] += [url, 'Error: File already exists.']
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