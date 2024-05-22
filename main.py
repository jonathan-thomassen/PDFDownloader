"""Application for scraping PDFs from a CSV file with URLs."""


from pathlib import Path
import sys

import downloader
import validator


CONNECTION_LIMIT = 8
DEFAULT_PDF_PATH = "./PDFs/"


def main():
    url_csvpath = Path()
    md5_csvpath = Path()
    overwrite = False
    validate = False
    only_validate = False
    pdf_dir = Path(DEFAULT_PDF_PATH)

    if len(sys.argv) > 1:
        if Path(sys.argv[1]).is_file():
            only_validate = False
            url_csvpath = Path(sys.argv[1])

            if "-v" in sys.argv[2:]:
                i = 2
                for arg in sys.argv[2:]:
                    if arg == "-v":
                        break
                    i += 1

                if Path(sys.argv[i + 1]).is_file():
                    md5_csvpath = Path(sys.argv[i + 1])

                    validate = True
                    print("Validation flag set. Will validate results after "
                          "downloading PDFs.")
                else:
                    raise SystemError("Path is not a file.")
            else:
                validate = False

            if "-d" in sys.argv[2:]:
                i = 2
                for arg in sys.argv[2:]:
                    if arg == "-d":
                        break
                    i += 1

                if Path(sys.argv[i + 1]):
                    pdf_dir = Path(sys.argv[i + 1])
                    print("Output directory set. PDFs will be downloaded to "
                          "this directory")
                else:
                    raise SystemError("Path is not valid.")

            if "-overwrite" in sys.argv[2:]:
                print("Overwrite flag set. Downloader will overwrite old "
                      "files.")
                overwrite = True
            else:
                overwrite = False
        elif sys.argv[1] == "-V":
            if len(sys.argv) > 2:
                if Path(sys.argv[2]).is_file():
                    md5_csvpath = Path(sys.argv[2])
                    only_validate = True
                    print("Upper-case validation flag set. Will skip download "
                          "phase and validate existing files in PDF folder.")
                else:
                    raise SystemError("Path to validation CSV is not a file.")
            else:
                raise SystemError("Path to validation CSV not given.")
        else:
            raise SystemError("Arguments invalid.")
    else:
        raise SystemError("No arguments given.")

    if only_validate:
        validator.validate_pdfs(md5_csvpath, pdf_dir=pdf_dir)
    else:
        downloader.download_pdfs(url_csvpath, pdf_dir=pdf_dir,
                                 connection_limit=CONNECTION_LIMIT,
                                 overwrite=overwrite)
        if validate:
            validator.validate_pdfs(md5_csvpath, pdf_dir=pdf_dir)


if __name__ == "__main__":
    main()
