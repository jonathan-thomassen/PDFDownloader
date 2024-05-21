"""Module providing PDF scraper functionality."""


from pathlib import Path
import sys
import time

import downloader
import validator


# TODO: Unit tests, being able to choose csv files
# TODO: Progress bars, more verbosity when establishing connection


MD5_CSVPATH = "./GRI_2017_2020_MD5_20220515.csv"


def main():
    start_time: float = time.time()

    url_csvpath: Path
    overwrite: bool

    if len(sys.argv) > 1:
        if Path(sys.argv[1]).is_file():
            url_csvpath = Path(sys.argv[1])
        else:
            raise SystemError("Path is not a file.")
    else:
        raise SystemError("Path to CSV file must be given as first argument.")

    if "-o" in sys.argv[2:]:
        print("Overwrite flag set. Downloader will overwrite old files.")
        overwrite = True
    else:
        overwrite = False

    if "-v" in sys.argv[2:]:
        print("Validation flag set. Will validate results.")
        validate = True
    else:
        validate = False

    downloader.download(url_csvpath, overwrite=overwrite)

    if validate:
        validator.validate(MD5_CSVPATH)

    end_time: float = time.time()
    print(
        "Time elapsed since application start: "
        f"{(end_time - start_time):.3f} seconds"
    )


if __name__ == "__main__":
    main()
