from typing import Optional, List


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


# Exceptions


class NotExpectedError(ApplicationError):
    pass


class InvalidError(UserError):
    def __init__(self, name: str, value: str, msg: Optional[str] = None):
        super().__init__(f"Invalid, {name}({value})" + (f": {msg}" if msg else ""))


class NotExistError(UserError):
    def __init__(self, name: str, msg: Optional[str] = None):
        super().__init__(f"Not Exist, {name}" + (f": {msg}" if msg else ""))


class DuplicatedError(UserError):
    def __init__(self, name: str, value: str, msg: Optional[str] = None):
        super().__init__(f"Duplicated, {name}({value})" + (f": {msg}" if msg else ""))


class FailedError(UserError):
    def __init__(self, reason: str, msg: Optional[str] = None):
        super().__init__(f"{reason} Failed" + (f": {msg}" if msg else ""))
