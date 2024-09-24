from typing import Optional


# Exception Types


class ApplicationError(Exception):
    def __init__(self, msg: str):
        super().__init__(
            f"{msg}\n"
            + "    : This error occurred due to application.\n"
            + "      Please new issue to https://github.com/taehee-won/MemRegGen/issues"
        )


class UserError(Exception):
    def __init__(self, msg: str):
        super().__init__(
            f"{msg}\n"
            + "    : This error occurred due to invalid input.\n"
            + "      Please check your input and try again."
        )


# ApplicationError Exceptions


class NotExpectedError(ApplicationError):
    pass


# UserError Exceptions


class InvalidFileExtensionError(UserError):
    def __init__(self, file_extension: str, msg: Optional[str] = None):
        super().__init__(
            f"Invalid, File Extension({file_extension})" + (f": {msg}" if msg else "")
        )


class NotExistFileError(UserError):
    def __init__(self, path: str, msg: Optional[str] = None):
        super().__init__(f"Not Exist, File({path})" + (f": {msg}" if msg else ""))


class FileReadError(UserError):
    def __init__(self, path: str, msg: Optional[str] = None):
        super().__init__(f"Read Failed, File({path})" + (f": {msg}" if msg else ""))


class FileWriteError(UserError):
    def __init__(self, path: str, msg: Optional[str] = None):
        super().__init__(f"Write Failed, File({path})" + (f": {msg}" if msg else ""))


class NotExistCSVRowError(UserError):
    def __init__(self, path: str, msg: Optional[str] = None):
        super().__init__(f"Not Exist, File({path})" + (f": {msg}" if msg else ""))


class NotExistCSVKeyError(UserError):
    def __init__(self, key: str, msg: Optional[str] = None):
        super().__init__(f"Not Exist, Key({key})" + (f": {msg}" if msg else ""))


class InvalidCSVRowError(UserError):
    def __init__(self, row: str, msg: Optional[str] = None):
        super().__init__(
            f"Invalid, Row({', '.join(row)})" + (f": {msg}" if msg else "")
        )


class NotExistArgumentError(UserError):
    def __init__(self, name: str, msg: Optional[str] = None):
        super().__init__(f"Not Exist, Argument({name})" + (f": {msg}" if msg else ""))


class InvalidArgumentError(UserError):
    def __init__(self, name: str, value: str, msg: Optional[str] = None):
        super().__init__(
            f"Invalid, Argument, Name({name}), Value({value})"
            + (f": {msg}" if msg else "")
        )


class InvalidArgumentTypeError(UserError):
    def __init__(
        self,
        name: str,
        value: str,
        expected: type,
        msg: Optional[str] = None,
    ):
        super().__init__(
            f"Invalid, Argument Type({type(value)})"
            + f", Name({name}), Value({value}), Expected Type({expected}))"
            + (f": {msg}" if msg else "")
        )


class InvalidHexStrError(UserError):
    def __init__(self, value: str, msg: Optional[str] = None):
        super().__init__(f"Invalid, Hexadecimal({value})" + (f": {msg}" if msg else ""))


class InvalidIntStrError(UserError):
    def __init__(self, value: str, msg: Optional[str] = None):
        super().__init__(f"Invalid, Integer({value})" + (f": {msg}" if msg else ""))


class InvalidDefineError(UserError):
    def __init__(self, define: str, msg: Optional[str] = None):
        super().__init__(f"Invalid Define({define})" + (f": {msg}" if msg else ""))


class InvalidKindError(UserError):
    def __init__(self, kind: str, msg: Optional[str] = None):
        super().__init__(f"Invalid Kind({kind})" + (f": {msg}" if msg else ""))


class DuplicatedNameError(UserError):
    def __init__(self, name: str, msg: Optional[str] = None):
        super().__init__(
            f"Duplicated, Definition({name})" + (f": {msg}" if msg else "")
        )


class InvalidNameError(UserError):
    def __init__(self, name: str, msg: Optional[str] = None):
        super().__init__(f"Invalid, Name({name})" + (f": {msg}" if msg else ""))


class NotExistAliasError(UserError):
    def __init__(self, alias: str, msg: Optional[str] = None):
        super().__init__(f"Not Exist, Alias({alias})" + (f": {msg}" if msg else ""))


class NotExistBookmarkError(UserError):
    def __init__(self, bookmark: str, msg: Optional[str] = None):
        super().__init__(
            f"Not Exist, Bookmark({bookmark})" + (f": {msg}" if msg else "")
        )


class InvalidAlignError(UserError):
    def __init__(self, align: int, value: str, msg: Optional[str] = None):
        super().__init__(
            f"Invalid, Align({align}) of Value({value})" + (f": {msg}" if msg else "")
        )
