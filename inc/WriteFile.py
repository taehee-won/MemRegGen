from os import mkdir
from os.path import dirname, exists

from inc.Exceptions import FailedError


class WriteFile:
    def __init__(self, path: str) -> None:
        self._path: str = path

    @property
    def path(self) -> str:
        return self._path

    def write(self, contents: str) -> None:
        if (dir := dirname(self._path)) and not exists(dir):
            mkdir(dir)

        try:
            with open(self._path, "w") as file:
                file.write(contents)

        except Exception as e:
            raise FailedError("Write", f"file({self._path}): {e}")
