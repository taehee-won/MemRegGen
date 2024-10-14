from typing import Final, Dict, Optional, Type, Tuple
from argparse import Namespace

from inc import InvalidError, NotExistError
from inc import Str


class PktConfig:
    # fmt: off
    _rules: Final[Dict[str, Tuple[Type, Optional[bool], Optional[str]]]] = {
        "name":       (str,  True,  "upper"),
        "mask":       (str,  False, "upper"),
        "shift":      (str,  False, "upper"),
        "raw":        (str,  False, "upper"),
        "value":      (str,  False, "upper"),
        "guard":      (str,  False, "upper"),
        "notes":      (str,  True,  None),
        "annotation": (bool, None,  None),
        "debug":      (bool, None,  None),
    }
    # fmt: on

    def _invalid_args(self, args: Namespace) -> None:
        for name, value in PktConfig._rules.items():
            expected_type = value[0]
            allow_empty = value[1]
            expected_case = value[2]

            if getattr(args, name, None) is None:
                raise NotExistError("Argument", f"{name} should not be none")

            value = getattr(args, name)

            if not isinstance(value, expected_type):
                raise InvalidError(
                    "Argument Type",
                    value,
                    f"{name} should be {expected_type} type",
                )

            if allow_empty is not None and not allow_empty and not value:
                raise NotExistError("Argument", f"{name} should not be empty")

            if (
                type(value) == str
                and value
                and expected_case
                and not getattr(value, f"is{expected_case}")()
            ):
                raise InvalidError(
                    "Argument",
                    value,
                    f"{name} should be {expected_case} cases",
                )

    def _set_args(self, args: Namespace) -> None:
        self._name: str = args.name
        self._mask: str = args.mask
        self._shift: str = args.shift
        self._raw: str = args.raw
        self._value: str = args.value
        self._guard: str = args.guard
        self._notes: str = args.notes
        self._annotation: bool = args.annotation
        self._debug: bool = args.debug

    def __init__(self, args: Namespace) -> None:
        self._invalid_args(args)
        self._set_args(args)

    def __str__(self) -> str:
        return Str.from_rows(
            [
                [name, str(getattr(self, name))]
                for name in PktConfig._rules.keys()
                if not (
                    isinstance(getattr(self, name), str) and not getattr(self, name)
                )
            ],
            separator=" : ",
        ).contents

    @property
    def name(self) -> str:
        return self._name

    @property
    def mask(self) -> str:
        return self._mask

    @property
    def shift(self) -> str:
        return self._shift

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def value(self) -> str:
        return self._value

    @property
    def guard(self) -> str:
        return self._guard

    @property
    def notes(self) -> str:
        return self._notes

    @property
    def annotation(self) -> bool:
        return self._annotation

    @property
    def debug(self) -> bool:
        return self._debug
