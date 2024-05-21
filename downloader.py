"""PDF downloader module."""


import csv
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

import grequests
from grequests import AsyncRequest
from requests.adapters import HTTPAdapter, Retry


class UrlEntry:
    def __init__(self, pdf_id: str):
        self.pdf_id = pdf_id
        self.urls = []

    def add(self, url: str) -> None:
        self.urls.append(url)


class ResultEntry:
    def __init__(self, pdf_id: str):
        self.pdf_id = pdf_id
        self.results = {}

    def add(self, url: str, result: str) -> None:
        self.results.update({url: result})


urls: list[UrlEntry] = []
results: list[ResultEntry] = []
requests: list[dict[str, str | AsyncRequest]] = []

results_csv_name = f"Results_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

session = grequests.Session()
retries = Retry(total=5, backoff_factor=0.1)
session.mount(prefix="http://", adapter=HTTPAdapter(max_retries=retries))
session.mount(prefix="https://", adapter=HTTPAdapter(max_retries=retries))
http_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,image/apng,*/*;q=0.8,"
    "application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-DK,en;q=0.9,da-DK;q=0.8,da;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Dnt": "1",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
}


def read_url_csv(filepath: Path,
                 delimiter: str = ",", quotechar: str =',') -> None:
    with open(
        file=filepath, newline="", errors="ignore", encoding="utf-8"
    ) as csv_file:
        csv_reader = csv.reader(csv_file,
                                delimiter=delimiter, quotechar=quotechar)
        i = 0
        for row in csv_reader:
            if i > 0:
                urls.append(UrlEntry(row[0]))
                for element in row[1:]:
                    urls[-1].add(element)
            i += 1


def write_results_csv() -> None:
    with open(results_csv_name, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(
            csv_file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        csv_writer.writerow(["Id", "URL_1", "Result_1", "URL_2", "Result_2"])
        for result_entry in results:
            csv_row = []
            csv_row.append(result_entry.pdf_id)

            for url, result in result_entry.results.items():
                csv_row.append(url)
                csv_row.append(result)

            while len(csv_row) < 5:
                csv_row.append("")

            csv_writer.writerow(csv_row)


def write_file(content: Any,
               filepath: Path,
               url: str,
               pdf_id: str,
               overwrite: bool = False
               ) -> None:
    if overwrite:
        pdf_writer_arg = "wb"
    else:
        pdf_writer_arg = "xb"

    if not filepath.suffix.upper() == ".PDF":
        filepath = filepath.with_suffix(".pdf")

    try:
        with open(filepath, pdf_writer_arg) as f:
            f.write(content)
    except FileExistsError:
        print("Id: " + pdf_id + ". File already exists: " + filepath.name)
        results[-1].add(url, "Error: File already exists.")
    else:
        print("Id: " + pdf_id + ". File successfully downloaded: " + url)
        results[-1].add(url, "File successfully downloaded.")


def create_request(url: str,
                   pdf_id: str,
                   pdf_dir: Path,
                   overwrite: bool,
                   ) -> AsyncRequest | None:
    if url.upper().startswith("HTTP"):
        if url.upper().startswith("HTTP:"):
            url = f"https:{url[5:]}"

        file_id = pdf_id
        while len(file_id) < 4:
            file_id = f"0{file_id}"
        filename = f"{file_id}_{url.split('/')[-1]}"

        if not filename.upper().endswith(".PDF"):
            filename += ".pdf"
        if not overwrite:
            filepath = pdf_dir.joinpath(filename)
            if filepath.exists():
                print(f"Id: {pdf_id}. File already exists: " f"{filename}")
                results[-1].add(url, "Error: File already exists.")
                return None

            print(f"Id: {pdf_id}. Sending 'GET' request: " f"{url}")
            request = grequests.get(
                url,
                timeout=(6.05, 120),
                verify=False,
                headers=http_headers,
            )
            return request
    else:
        print(
            f"Id: {pdf_id}. Hyperlink not a valid URL to a PDF document: ",
            end="",
        )
        if url:
            print(url)
            results[-1].add(
                url,
                "Error: Hyperlink not a valid URL to a PDF document.",
            )
        else:
            print("(blank)")
            results[-1].add(url, "Error: URL blank.")


def download(csvpath: Path, pdf_dir: Path | None = None,
             connection_limit: int = 8, overwrite: bool = False) -> None:
    if pdf_dir is None:
        pdf_dir = Path("./PDFs/")
    elif not pdf_dir.is_dir():
        raise SystemError("Path is not a directory.")

    read_url_csv(csvpath)

    for url_entry in urls:
        results.append(ResultEntry(url_entry.pdf_id))
        for url in url_entry.urls:
            request = create_request(url, url_entry.pdf_id, pdf_dir, overwrite)
            if request is not None:
                requests.append({"id": url_entry.pdf_id,
                                 "url": url,
                                 "request": request})

            # TODO: Remove this break and actually process both columns of urls.
            break

    # Perform request actions
    for request_list_no, response in grequests.imap_enumerated(
        [r["request"] for r in requests],
        size=connection_limit
    ):
        if response:
            pdf_id = requests[request_list_no]["id"]
            url = requests[request_list_no]["url"]

            try:
                content_type: str = response.headers["Content-Type"]
            except KeyError:
                print(
                    f"Id: {pdf_id}. Response from server does not contain a "
                    f"'Content-Type' field: {url}"
                )
                results[-1].add(
                    pdf_id,
                    "Error: Response from "
                    "server does not contain a 'Content-Type' field.",
                )
            else:
                if "application/pdf" in content_type:
                    content = response.content

                    id_string = str(pdf_id)
                    while len(id_string) < 4:
                        id_string = "0" + id_string

                    filename = f"{id_string}_{url.split('/')[-1]}"

                    filepath = pdf_dir.joinpath(filename)

                    if sys.getsizeof(content) > 33:
                        write_file(content, filepath, url, pdf_id)

                else:
                    print(
                        f"Id: {pdf_id}. File linked to in URL is not a PDF "
                        f"document: {url}"
                    )
                    results[-1].add(
                        url, "Error: "
                             "File linked to in URL is not a PDF document."
                    )

    write_results_csv()