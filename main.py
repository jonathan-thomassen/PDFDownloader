"""Module providing PDF scraper functionality."""


from pathlib import Path
import sys

import downloader
import validator


# TODO: Unit tests, Progress bars + Make application more verbose

CONNECTION_LIMIT = 8


def main():
    url_csvpath: Path = Path()
    md5_csvpath: Path = Path()
    overwrite: bool = False
    validate: bool = False
    only_validate: bool = False

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

            if "-o" in sys.argv[2:]:
                print("Overwrite flag set. Downloader will overwrite old "
                      "files.")
                overwrite = True
            else:
                overwrite = False
        elif "-V" in sys.argv[2:]:
            i = 2
            for arg in sys.argv[2:]:
                if arg == "-V":
                    break
                i += 1

            if Path(sys.argv[i + 1]).is_file():
                md5_csvpath = Path(sys.argv[i + 1])

                only_validate = True
                print("Upper-case validation flag set. Will skip download "
                      "phase and validate existing files in PDF folder.")
            else:
                raise SystemError("Path is not a file.")
        else:
            raise SystemError("Arguments invalid.")
    else:
        raise SystemError("No arguments given.")

    if only_validate:
        validator.validate_pdfs(md5_csvpath)
    else:
        downloader.download_pdfs(url_csvpath, connection_limit=CONNECTION_LIMIT,
                                 overwrite=overwrite)
        if validate:
            validator.validate_pdfs(md5_csvpath)


if __name__ == "__main__":
    main()
