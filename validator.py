"""PDF validator module."""


from pathlib import Path
import csv
import hashlib
import re


def validate_pdfs(csv_path: Path, pdf_dir: str = "./PDFs/",
                  delimiter: str = ",", quotechar: str = '"'):
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=delimiter,
                                quotechar=quotechar)
        md5s = {}
        i = 0
        for row in csv_reader:
            if i > 0:
                md5s.update({row[0]: row[1]})
            i = 1

    path = Path(pdf_dir)
    files = [f for f in path.iterdir() if f.is_file()]

    val_success = 0
    val_failed = 0

    for pdf_id, pdf_hash in md5s.items():
        id_string = str(pdf_id)
        while len(id_string) < 4:
            id_string = "0" + id_string
        files_accounted_for: list[Path] = []
        file_missing = True
        for file in files:
            regex_string = r"\b" + id_string + r"[^/]*\.pdf$"
            if re.match(regex_string, file.name):
                file_missing = False
                with open(pdf_dir + file.name, "rb") as pdf:
                    md5hash = hashlib.md5(pdf.read()).hexdigest()
                    if md5hash == pdf_hash.lower():
                        print(
                            f"Id: {pdf_id}. File: '{file.name}' Successful "
                            "validation."
                        )
                        val_success += 1
                    else:
                        print(
                            f"Id: {pdf_id}. File: '{file.name}' Validation "
                            "failed. MD5 hash mismatch."
                        )
                        val_failed += 1
                files_accounted_for.append(file)
        if file_missing:
            print(
                f"Id: {pdf_id}. MD5 hash: '{pdf_hash}' "
                "File missing in folder."
            )
            val_failed += 1
        for file in files_accounted_for:
            files.remove(file)

    for file in files:
        if file.suffix.upper() == ".PDF":
            print(
                f"File: '{file.name}' does not exist in validation database.")
            val_failed += 1

    print(
        f"Validation results: {str(val_success)} file(s) succeeded. "
        f"{str(val_failed)} file(s) failed."
    )
