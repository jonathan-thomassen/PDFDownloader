"""Module providing PDF scraper functionality."""


from pathlib import Path
import sys
import time

import downloader
import validator


# TODO: Unit tests, Progress bars + Make application more verbose


def main():
    start_time: float = time.time()

    url_csvpath: Path
    md5_csvpath: Path = Path()
    overwrite: bool
    validate: bool
    only_validate: bool

    if len(sys.argv) > 1:
        if Path(sys.argv[1]).is_file():
            url_csvpath = Path(sys.argv[1])
        else:
            raise SystemError("The URL-CSV path is not a valid path to a file.")
    else:
        raise SystemError("Path to URL-CSV file must "
                          "be given as first argument.")

    if "-v" in sys.argv[2:]:
        i = 2
        for arg in sys.argv[2:]:
            if arg == "-v":
                break
            i += 1

        if Path(sys.argv[i + 1]).is_file():
            md5_csvpath = Path(sys.argv[i + 1])

            validate = True
            print("Validation flag set. Will validate results "
                  "after downloading PDFs.")
        else:
            raise SystemError("Path is not a file.")
    else:
        validate = False

    if "-V" in sys.argv[2:]:
        i = 2
        for arg in sys.argv[2:]:
            if arg == "-V":
                break
            i += 1

        if Path(sys.argv[i + 1]).is_file():
            md5_csvpath = Path(sys.argv[i + 1])

            only_validate = True
            print("Capital validation flag set. Will skip download phase and "
                  "validate existing files in PDF folder.")
        else:
            raise SystemError("Path is not a file.")
    else:
        only_validate = False

    if "-o" in sys.argv[2:]:
        print("Overwrite flag set. Downloader will overwrite old files.")
        overwrite = True
    else:
        overwrite = False

    if only_validate:
        validator.validate_pdfs(md5_csvpath)
    else:
        downloader.download_pdfs(url_csvpath, overwrite=overwrite)
        if validate:
            validator.validate_pdfs(md5_csvpath)

    end_time: float = time.time()
    print(
        "Time elapsed since application start: "
        f"{(end_time - start_time):.3f} seconds"
    )


if __name__ == "__main__":
    main()
