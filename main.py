'''Module providing PDF scraper functionality.'''

import grequests
import csv
import datetime
import time
import sys
import hashlib
import pathlib
import re

# from requests.exceptions import ConnectionError as RequestConnectionError
# from requests.exceptions import RetryError
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime
from pathlib import Path

# TODO: Multi-threading, unit tests, being able to choose csv files,
#       progress bars, more verbosity when establishing connection

# Currently missing: 128: Sends to script which redirects to PDF?
# Maybe Google Chrome magic is what makes it work?

start_time = time.time()

URL_CSV_PATH = './GRI_2017_2020.csv'
MD5_CSV_PATH = './GRI_2017_2020_MD5_20220515.csv'
PDF_FOLDER = './PDFs/'
CONNECTION_LIMIT = 8

pdf_writer_arg = 'xb'
overwrite = False
run_validation = False

url_list = []
result_list = []
request_dict = []

results_csv_name = 'Results_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
session = grequests.Session()
retries = Retry(total=5, backoff_factor=0.1)
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
http_headers = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,\
    image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
  'Accept-Language': 'en-DK,en;q=0.9,da-DK;q=0.8,da;q=0.7,en-US;q=0.6',
  'Cache-Control': 'no-cache',
  'Dnt': '1',
  'Pragma': 'no-cache',
  'Upgrade-Insecure-Requests': '1',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

if len(sys.argv) > 1:
  argument = sys.argv[1]
  if argument:
    if argument == '-o':
      print('Overwrite flag set. Downloader will overwrite old files.')
      pdf_writer_arg = 'wb'
      overwrite = True
    elif argument == '-v':
      print('Validation flag set. Running validation.')
      run_validation = True

class UrlEntry:
  def __init__(self, pdf_id):
    self.pdf_id = pdf_id
    self.urls = []

  def AddUrl(self, url):
    self.urls.append(url)

class ResultEntry:
  def __init__(self, pdf_id):
    self.pdf_id = pdf_id
    self.results = {}

  def AddResult(self, url, result):
    self.results.update({url: result})

def read_url_csv(file_path, delimiter, quotechar):
  with open(file_path, newline='', errors='ignore', encoding='utf-8')\
  as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=delimiter, quotechar=quotechar)
    n = 0
    for row in csv_reader:
      if n > 0:
        url_list.append(UrlEntry(row[0]))
        for element in row[1:]:
          url_list[-1].AddUrl(element)
      n += 1

def write_results_csv():
  with open(results_csv_name, 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(['Id', 'URL_1', 'Result_1', 'URL_2', 'Result_2'])
    for result_entry in result_list:
      csv_row = []
      csv_row.append(result_entry.pdf_id)

      for url, result in result_entry.results.items():
        csv_row.append(url)
        csv_row.append(result)

      while len(csv_row) < 5:
        csv_row.append('')

      csv_writer.writerow(csv_row)

def write_pdf_to_file(content, filename, url, pdf_id):
  if not filename.upper().endswith('.PDF'):
    filename += '.pdf'
  try:
    with open(PDF_FOLDER + filename, pdf_writer_arg) as f:
      f.write(content)
  except FileExistsError:
    print('Id: ' + pdf_id + '. File already exists: ' + filename)
    result_list[-1].AddResult(url, 'Error: File already exists.')
  else:
    print('Id: ' + pdf_id + '. File successfully downloaded: ' + url)
    result_list[-1].AddResult(url, 'File successfully downloaded.')

def does_file_exist(local_filename):
  path = Path(PDF_FOLDER + local_filename)
  if path.is_file():
    return True
  return False

def download_pdfs():
  for url_entry in url_list:
    result_list.append(ResultEntry(url_entry.pdf_id))
    for url in url_entry.urls:
      # TODO: Eventuelt lav check om til funktion
      if url.upper().startswith('HTTP'):
        if url.upper().startswith('HTTP:'):
          url = 'https:' + url[5:]

        id_string = str(url_entry.pdf_id)
        while len(id_string) < 4:
          id_string = '0' + id_string

        local_filename = id_string + '_' + url.split('/')[-1]
        if not local_filename.upper().endswith('.PDF'):
          local_filename += '.pdf'
        if not overwrite:
          if does_file_exist(local_filename):
            print('Id: ' + url_entry.pdf_id + '. File already exists: '
                  + local_filename)
            result_list[-1].AddResult(url, 'Error: File already exists.')
            break
          # Create request action and add to list
          print('Id: ' + url_entry.pdf_id + '. Sending \'GET\' request: ' + url)
          request_action = grequests.get(url, timeout=(6.05, 120),
                                         verify=False, headers=http_headers)

          request_dict.append((url_entry.pdf_id, url, request_action))
      else:
        print('Id: ' + url_entry.pdf_id + '. Hyperlink not a valid URL to a ' +
              'PDF document: ', end='')
        if url:
          print(url)
          result_list[-1].AddResult(url, 'Error: Hyperlink not a valid URL ' +
                                         'to a PDF document.')
        else:
          print('(blank)')
          result_list[-1].AddResult(url, 'Error: URL blank.')
      break

  # Perform request actions
  for request_list_no, response in \
    grequests.imap_enumerated([t[2] for t in request_dict],
                              size=CONNECTION_LIMIT):
    if response:
      pdf_id = request_dict[request_list_no][0]
      url = request_dict[request_list_no][1]

      try:
        content_type = response.headers['Content-Type']
      except KeyError:
        print('Id: ' + pdf_id + '. Response from server does not contain a '
              '\'Content-Type\' field: ' + url)
        result_list[-1].AddResult(pdf_id, 'Error: Response from server does ' +
                                 'not contain a \'Content-Type\' field.')
        pass
      else:
        if 'application/pdf' in content_type:
          content = response.content

          id_string = str(pdf_id)
          while len(id_string) < 4:
            id_string = '0' + id_string

          filename = id_string + '_' + url.split('/')[-1]

          if sys.getsizeof(content) > 33:
            write_pdf_to_file(content, filename, url, pdf_id)

        else:
          print('Id: ' + pdf_id + '. File linked to in URL is not ' +
                'a PDF document: ' + url)
          result_list[-1].AddResult(url, 'Error: File linked to in URL is ' +
                                   'not a PDF document.')

  write_results_csv()

def validate_results(csv_file_path, pdf_folder, delimiter, quotechar):
  with open(csv_file_path, newline='', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=delimiter, quotechar=quotechar)
    md5_dict = {}
    n = 0
    for row in csv_reader:
      if n > 0:
        md5_dict.update({row[0]: row[1]})
      n = 1

  path = pathlib.Path(pdf_folder)
  files = [f for f in path.iterdir() if f.is_file()]

  val_success = 0
  val_failed = 0

  for pdf_id, pdf_hash in md5_dict.items():
    id_string = str(pdf_id)
    while len(id_string) < 4:
      id_string = '0' + id_string
    files_accounted_for = []
    file_missing = True
    for file in files:
      regex_string = r'\b' + id_string +  r'[^/]*\.pdf$'
      if re.match(regex_string, file.name):
        file_missing = False
        with open(pdf_folder + file.name, 'rb') as pdf:
          md5hash = hashlib.md5(pdf.read()).hexdigest()
          if md5hash == pdf_hash.lower():
            print('Id: ' + pdf_id + '. File: \'' + file.name +
                  '\' Successful validation.')
            val_success += 1
          else:
            print('Id: ' + pdf_id + '. File: \'' + file.name +
                  '\' Validation failed. MD5 hash mismatch.')
            val_failed += 1
        files_accounted_for.append(file)
    if file_missing:
      print('Id: ' + pdf_id + '. MD5 hash: \'' + pdf_hash +
                  '\' File missing in folder.')
      val_failed += 1
    for file in files_accounted_for:
      files.remove(file)

  for file in files:
    if file.suffix.upper() == '.PDF':
      print('File: \'' + file.name +
            '\' does not exist in validation database.')
      val_failed += 1

  print('Validation results: ' + str(val_success) + ' file(s) succeeded. '
        + str(val_failed) + ' file(s) failed.')

if run_validation:
  validate_results(MD5_CSV_PATH, PDF_FOLDER, ',', '\"')
else:
  read_url_csv(URL_CSV_PATH, ',', '\"')
  download_pdfs()

print('Time elapsed since application start: '
      f'{(time.time() - start_time):.3f} seconds')
