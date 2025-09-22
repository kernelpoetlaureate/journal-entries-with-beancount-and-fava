"""Lightweight importer wrapper for future integration with beancount.ingest

This file provides a CSVImporter class with a minimal API similar to
beancount.ingest importers: it accepts a file and returns generated
beancount text. It currently uses the simpler scripts/importer.py logic.

Later this can be refactored to subclass beancount.ingest.Importer if the
beancount package is available in the environment.
"""
from typing import List
from pathlib import Path

from .importer import convert_csv_to_beancount


class CSVImporter:
    def __init__(self, mapping=None):
        self.mapping = mapping or {}

    def import_file(self, csv_path: str) -> str:
        # For now, write to a temporary file and return its contents
        csv_path = Path(csv_path)
        out_path = csv_path.with_suffix('.beancount')
        convert_csv_to_beancount(str(csv_path), str(out_path))
        return out_path.read_text(encoding='utf-8')


def import_to_string(csv_path: str) -> str:
    importer = CSVImporter()
    return importer.import_file(csv_path)
