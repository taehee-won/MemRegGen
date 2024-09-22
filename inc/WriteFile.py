from inc.Exceptions import FileWriteError


class WriteFile:
    def __init__(self, path: str) -> None:
        self._path: str = path

    @property
    def path(self) -> str:
        return self._path

    def write(self, contents: str) -> None:
        try:
            with open(self._path, "w") as file:
                file.write(contents)

        except Exception as e:
            raise FileWriteError(self._path, str(e))
