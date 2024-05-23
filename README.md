# Python PDF Downloader

This is a simple python script designed to download PDF files from a given CSV file.

* Downloads PDF files from a CSV list of URLs.
* Each URL can have a backup-link to be used in the case the main link fails.
* The script generates a CSV file with a list of results of the downloads.
* MD5 validation is available to validate the integrity of the downloaded files.

## Important security notice

TLS certificate verification is disabled for this application. Thus, it is highly recommended to only include URLs  
to sources you trust. The author takes no responsibility for any security breaches as a result of the use of this  
application.

## Usage

### Arguments

**main.py PATH_TO_URL_CSV**

Default output directory is "./PDFs/" which will be created if it doesn't exist. To set a different output directory  
use the *-d* flag, like so:  
**main.py PATH-TO-URL-CSV -d PATH-TO-OUTPUT-DIRECTORY**

To run validation on the downloaded files after downloading has completed, use the *-v* flag, like so:  
**main.py PATH-TO-URL-CSV -d PATH-TO-OUTPUT-DIRECTORY -v PATH-TO-VALIDATION-CSV**

To only run validation, without downloading any files, use capital-letter *-V*, like so:  
**main.py -d PATH-TO-PDF-DIRECTORY -V PATH-TO-VALIDATION-CSV**

If, when downloading, you would like the application to overwrite existing files, you can include the *-overwrite*  
flag as an argument, like so:  
**main.py PATH-TO-URL-CSV -d PATH-TO-OUTPUT-DIRECTORY -overwrite**

### Format of URL CSV file

| Id | PDF-Link-1 | PDF-Link-2 |
| - | - | - |
| 3 | http://www.thisisaurl.com/toa.pdf | https://thisisabackupurl.gov/tothesame.pdf |

The URL CSV file is expected to be comma-separated, using double-quation marks ( " ) for quotations.

### Format of MD5 CSV file

| Id | MD5 |
| - | - |
| 3 | 83224762B21413EC6ED3F43270EBC74F |

The MD5 CSV file is expected to be comma-separated and to not use any quotations.