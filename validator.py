"""PDF validator module."""


from dataclasses import dataclass
from pathlib import Path
import csv
import hashlib
import re


@dataclass()
class ValidatorConfig:
    csv_path: Path
    delimiter: str
    quotechar: str


def check_hash_match(pdf_hash: str, file: Path,
                     pdf_id: str) -> tuple[bool, bool]:
    id_string = str(pdf_id)
    while len(id_string) < 4:
        id_string = "0" + id_string

    regex_string = r"\b" + id_string + r"[^/]*\.pdf$"
    if re.match(regex_string, file.name):
        matching_filename = True
        with open(file, "rb") as pdf:
            md5hash = hashlib.md5(pdf.read()).hexdigest()
            if md5hash == pdf_hash.lower():
                print(f"Id: {pdf_id}. File: '{file.name}' Successful "
                      "validation.")
                result = True
            else:
                print(f"Id: {pdf_id}. File: '{file.name}' Validation "
                      "failed. MD5 hash mismatch.")
                result = False
    else:
        matching_filename = False
        result = False
    return (matching_filename, result)


def read_hash_csv(config: ValidatorConfig) -> dict[str, str]:
    with open(config.csv_path, newline="", encoding="utf-8") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=config.delimiter,
                                quotechar=config.quotechar)
        md5s = {}
        first_row = True
        for row in csv_reader:
            if not first_row:
                md5s.update({row[0]: row[1]})
            first_row = False

    return md5s


def validate_pdfs(csv_path: Path, pdf_dir: Path, delimiter: str = ",",
                  quotechar: str = '"'):
    if not pdf_dir.is_dir():
        raise SystemError("Path is not a directory.")

    config = ValidatorConfig(csv_path, delimiter, quotechar)
    md5s = read_hash_csv(config)

    files = [f for f in pdf_dir.iterdir() if f.is_file()]
    success = 0
    failed = 0

    for pdf_id, pdf_hash in md5s.items():
        files_matching_name: list[Path] = []
        for file in files:
            matching_filename, result = check_hash_match(
                pdf_hash, file, pdf_id)
            if matching_filename:
                files_matching_name.append(file)
                if result:
                    success += 1
                else:
                    failed += 1

        if len(files_matching_name) == 0:
            print(f"Id: {pdf_id}. MD5 hash: '{pdf_hash}' File missing in "
                  "folder.")
            failed += 1
        else:
            for file in files_matching_name:
                files.remove(file)

    for file in files:
        if file.suffix.upper() == ".PDF":
            print(
                f"File: '{file.name}' does not exist in validation database.")
            failed += 1

    print(f"Validation results: {str(success)} file(s) succeeded. "
          f"{str(failed)} file(s) failed.")
