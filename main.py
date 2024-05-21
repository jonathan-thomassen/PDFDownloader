"""Module providing PDF scraper functionality."""


from pathlib import Path
import sys
import time

import downloader
import validator


# TODO: Check both URLs, Unit tests, Progress bars
# TODO: More verbosity when establishing connection


def main():
    start_time: float = time.time()

    url_csvpath: Path
    md5_csvpath: Path = Path()
    overwrite: bool
    validate: bool

    if len(sys.argv) > 1:
        if Path(sys.argv[1]).is_file():
            url_csvpath = Path(sys.argv[1])
        else:
            raise SystemError("Path is not a file.")
    else:
        raise SystemError("Path to CSV file must be given as first argument.")

    if "-v" in sys.argv[2:]:
        i = 2
        for arg in sys.argv[2:]:
            if arg == "-v":
                break
            i += 1

        if Path(sys.argv[i + 1]).is_file():
            md5_csvpath = Path(sys.argv[1])

            validate = True
            print("Validation flag set. Will validate results.")
        else:
            raise SystemError("Path is not a file.")
    else:
        validate = False

    if "-o" in sys.argv[2:]:
        print("Overwrite flag set. Downloader will overwrite old files.")
        overwrite = True
    else:
        overwrite = False

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
