from typing import Final, Dict, Optional, Type, Tuple
from argparse import Namespace

from inc import (
    InvalidArgumentTypeError,
    NotExistArgumentError,
    InvalidArgumentError,
)
from inc import Str


class MemConfig:
    # fmt: off
    _rules: Final[Dict[str, Tuple[Type, Optional[bool], Optional[str]]]] = {
        "guard":      (str,  False, "upper"),
        "type":       (str,  True,  "upper"),
        "prefix":     (str,  True,  "upper"),
        "postfix":    (str,  True,  "upper"),
        "array":      (str,  False, "lower"),
        "bits":       (int,  False, None),
        "align":      (int,  False, None),
        "annotation": (bool, None,  None),
        "debug":      (bool, None,  None),
    }
    # fmt: on

    def _invalid_args(self, args: Namespace) -> None:
        for name, value in MemConfig._rules.items():
            expected_type = value[0]
            allow_empty = value[1]
            expected_case = value[2]

            if getattr(args, name, None) is None:
                raise NotExistArgumentError(name, f"{name} should not be none")

            value = getattr(args, name)

            if not isinstance(value, expected_type):
                raise InvalidArgumentTypeError(name, value, expected_type)

            if allow_empty is not None and not allow_empty and not value:
                raise NotExistArgumentError(name, f"{name} should not be empty")

            if (
                type(value) == str
                and value
                and not getattr(value, f"is{expected_case}")()
            ):
                raise InvalidArgumentError(
                    name, value, f"{name} should be {expected_case} cases"
                )

        if (value := getattr(args, (name := "bits"))) not in [64, 32]:
            raise InvalidArgumentError(name, value, f"{name} should be 64, 32")

        if (value := getattr(args, (name := "align"))) and (
            not value <= (limit := (16 if getattr(args, "bits") == 64 else 8))
        ):
            raise InvalidArgumentError(
                name, value, f"{name} should less or equal than {limit}"
            )

    def _set_args(self, args: Namespace) -> None:
        self._guard: str = args.guard
        self._prefix: str = args.prefix
        self._postfix: str = args.postfix
        self._type: str = args.type
        self._array: str = args.array
        self._bits: int = args.bits
        self._align: int = args.align
        self._annotation: bool = args.annotation
        self._debug: bool = args.debug

    def __init__(self, args: Namespace) -> None:
        self._invalid_args(args)
        self._set_args(args)

    @property
    def debug_str(self) -> str:
        return (
            Str.from_rows(
                [
                    [name, str(getattr(self, name))]
                    for name in [
                        "guard",
                        "prefix",
                        "postfix",
                        "array",
                        "bits",
                        "align",
                        "annotation",
                        "debug",
                    ]
                ],
                ": ",
            )
            .insert_guard("-")
            .insert_line("MemConfig")
            .add_guard("=")
            .contents
        )

    @property
    def guard(self) -> str:
        return self._guard

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def postfix(self) -> str:
        return self._postfix

    @property
    def type(self) -> str:
        return self._type

    @property
    def array(self) -> str:
        return self._array

    @property
    def bits(self) -> int:
        return self._bits

    @property
    def align(self) -> int:
        return self._align

    @property
    def annotation(self) -> bool:
        return self._annotation

    @property
    def debug(self) -> bool:
        return self._debug
