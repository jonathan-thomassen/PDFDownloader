'''Module providing PDF scraperfunctionality.'''

import requests
import csv
import datetime
import sys
import hashlib
import pathlib
import re

from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import RetryError
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime
from pathlib import Path
from url_entry import UrlEntry
from result_entry import ResultEntry

# TODO: Multi-threading, unit tests, being able to choose csv file,
#       progress bars, more verbosity when establishing connection

# Currently missing: 128: Sends to script which redirects to PDF?
# Maybe Google Chrome magic is what makes it work?

URL_CSV_PATH = './GRI_2017_2020.csv'
MD5_CSV_PATH = './GRI_2017_2020_MD5_20220515.csv'
PDF_FOLDER = './PDFs/'
PDF_WRITER_ARG = 'xb'
overwrite = False
RUN_VALIDATION = False

url_list = []
result_list = []

results_csv_name = 'Results_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
session = requests.Session()
retries = Retry(total=5, backoff_factor=0.1)
session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
http_headers = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,\
             image/avif,image/webp,image/apng,*/*;q=0.8,\
             application/signed-exchange;v=b3;q=0.7',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Accept-Language': 'en-DK,en;q=0.9,da-DK;q=0.8,da;q=0.7,en-US;q=0.6',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
  'Dnt': '1',
  'Pragma': 'no-cache',
  'Upgrade-Insecure-Requests': '1',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                 AppleWebKit/537.36 (KHTML, like Gecko) \
                 Chrome/124.0.0.0 Safari/537.36'
}

if len(sys.argv) > 1:
  argument = sys.argv[1]
  if argument is not None:
    if argument == '-o':
      print('Overwrite flag set. Downloader will overwrite old files.')
      PDF_WRITER_ARG = 'wb'
      overwrite = True
    elif argument == '-v':
      print('Validation flag set. Running validation.')
      RUN_VALIDATION = True

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
      csv_row.append(result_entry.id)

      for url, result in result_entry.results.items():
        csv_row.append(url)
        csv_row.append(result)

      while len(csv_row) < 5:
        csv_row.append('')

      csv_writer.writerow(csv_row)

def write_pdf_to_file(content, local_filename, url, url_id):
  try:
    with open(PDF_FOLDER + local_filename, PDF_WRITER_ARG) as f:
      f.write(content)
  except FileExistsError:
    print('Id: ' + url_id + '. File already exists: ' + local_filename)
    result_list[-1].AddResult(url, 'Error: File already exists.')
  else:
    print('Id: ' + url_id + '. File successfully downloaded: ' + url)
    result_list[-1].AddResult(url, 'File successfully downloaded.')

def does_file_exist(local_filename):
  path = Path(PDF_FOLDER + local_filename)
  if path.is_file():
    return True
  return False

def download_pdfs():
  for url_entry in url_list:
    result_list.append(ResultEntry(url_entry.id))
    for url in url_entry.urls:
      # TODO: Eventuelt lav check om til funktion
      if url.upper().startswith('HTTP'):
        if url.upper().startswith('HTTP:'):
          url = 'https:' + url[5:]

        id_string = str(url_entry.id)
        while len(id_string) < 4:
          id_string = '0' + id_string

        local_filename = id_string + '_' + url.split('/')[-1]
        if local_filename.upper().endswith('.PDF') is False:
          local_filename += '.pdf'
        if overwrite is False:
          if does_file_exist(local_filename):
            print('Id: ' + url_entry.id + '. File already exists: '
                  + local_filename)
            result_list[-1].AddResult(url, 'Error: File already exists.')
            break
        try:
          # Acquire response from server
          print('Id: ' + url_entry.id + '. Sending \'GET\' request: ' + url)
          response = session.get(url, timeout=(6.05, 120),
                                 verify=False, headers=http_headers)
        # TODO: Læs op på session og ConnectionError
        except (RequestConnectionError, RetryError):
          print('Id: ' + url_entry.id + '. Connection error while trying to ' +
                'download the following file: ' + url)
          result_list[-1].AddResult(url, 'Error: File could not be ' +
                                   'downloaded (connection error).')
          pass
        else:
          try:
            content_type = response.headers['Content-Type']
          except KeyError:
            print('Id: ' + url_entry.id + '. Response from server does not ' +
                  'contain a \'Content-Type\' field: ' + url)
            result_list[-1].AddResult(url, 'Error: Response from server does ' +
                                     'not contain a \'Content-Type\' field.')
            pass
          else:
            if 'application/pdf' in content_type:
              content = response.content
              if sys.getsizeof(content) > 33:
                write_pdf_to_file(content, local_filename, url, url_entry.id)
                break
            print('Id: ' + url_entry.id + '. File linked to in URL is not ' +
                  'a PDF document: ' + url)
            result_list[-1].AddResult(url, 'Error: File linked to in URL is ' +
                                     'not a PDF document.')
      else:
        print('Id: ' + url_entry.id + '. Hyperlink not a valid URL to a PDF ' +
              'document: ', end='')
        if url is not '':
          print(url)
          result_list[-1].AddResult(url, 'Error: Hyperlink not a valid URL ' +
                                   'to a PDF document.')
        else:
          print('(blank)')
          result_list[-1].AddResult(url, 'Error: URL blank.')
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
    for file in files:
      regex_string = r'\b' + id_string +  r'[^/]*\.pdf$'
      if re.match(regex_string, file.name):
        with open(pdf_folder + file.name, 'rb') as pdf:
          md5hash = hashlib.md5(pdf.read()).hexdigest()
          if md5hash is pdf_hash.lower():
            print('Id: ' + pdf_id + '. File: \'' + file.name +
                  '\' Successful validation.')
            val_success += 1
          else:
            print('Id: ' + pdf_id + '. File: \'' + file.name +
                  '\' Validation failed. MD5 hash mismatch.')
            val_failed += 1
        files_accounted_for.append(file)
    for file in files_accounted_for:
      files.remove(file)

  for file in files:
    if file.suffix.upper() is '.PDF':
      print('File: \'' + file.name +
            '\' does not exist in validation database.')
      val_failed += 1

  print('Validation results: ' + str(val_success) + ' file(s) succeeded. '
        + str(val_failed) + ' file(s) failed.')

if RUN_VALIDATION:
  validate_results(MD5_CSV_PATH, PDF_FOLDER, ',', '\"')
else:
  read_url_csv(URL_CSV_PATH, ',', '\"')
  download_pdfs()
