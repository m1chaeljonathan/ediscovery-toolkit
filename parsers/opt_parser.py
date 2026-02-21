import csv
from pathlib import Path
from dataclasses import dataclass


@dataclass
class OptRecord:
    begdoc: str
    volume: str
    image_path: str
    first_page: bool
    page_count: int


def parse_opt(filepath: str) -> list[OptRecord]:
    path = Path(filepath)
    records = []
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue
            records.append(OptRecord(
                begdoc=row[0].strip(),
                volume=row[1].strip(),
                image_path=row[2].strip(),
                first_page=(row[3].strip().upper() == 'Y'),
                page_count=int(row[4].strip()) if len(row) > 4 and row[4].strip().isdigit() else 0,
            ))
    return records
