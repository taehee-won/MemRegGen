from typing import Tuple, List
from os.path import isfile
from hashlib import sha256
from csv import reader

from inc.Exceptions import NotExistFileError, FileReadError, NotExistCSVRowError


class ReadFile:
    def __init__(self, path: str) -> None:
        if not isfile(path):
            raise NotExistFileError(path)

        self._path: str = path

    @property
    def path(self) -> str:
        return self._path

    @property
    def hash(self) -> str:
        engine = sha256()
        with open(self._path, "rb") as file:
            for block in iter(lambda: file.read(4096), b""):
                engine.update(block)

        return engine.hexdigest()

    @property
    def contents(self) -> str:
        try:
            with open(self._path, "r", encoding="UTF-8-sig") as file:
                contents = file.read()

        except Exception as e:
            raise FileReadError(self._path, str(e))

        return contents

    @property
    def csv_contents(self) -> Tuple[List[str], List]:
        try:
            with open(self._path, "r", encoding="UTF-8-sig") as file:
                rows = [row for row in reader(file)]

        except Exception as e:
            raise FileReadError(self._path, str(e))

        if not len(rows):
            raise NotExistCSVRowError(self._path)

        csv_keys = rows[0]
        rows.pop(0)

        return csv_keys, [row for row in rows if any(cell.strip() for cell in row)]
