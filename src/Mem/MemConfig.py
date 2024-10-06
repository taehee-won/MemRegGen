from typing import Final, Dict, Optional, Type, Tuple
from argparse import Namespace

from inc import InvalidError, NotExistError
from inc import Str


class MemConfig:
    # fmt: off
    _rules: Final[Dict[str, Tuple[Type, Optional[bool], Optional[str]]]] = {
        "memory":     (str,  False, "upper"),
        "bits":       (int,  False, None),
        "align":      (int,  False, None),
        "plural":     (str,  False, "upper"),
        "array":      (str,  False, "lower"),
        "number":     (str,  False, "upper"),
        "prefix":     (str,  True,  "upper"),
        "postfix":    (str,  True,  "upper"),
        "guard":      (str,  False, "upper"),
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
                and not getattr(value, f"is{expected_case}")()
            ):
                raise InvalidError(
                    "Argument",
                    value,
                    f"{name} should be {expected_case} cases",
                )

        if (value := getattr(args, (name := "bits"))) not in [64, 32]:
            raise InvalidError("Argument", value, f"{name} should be 64, 32")

        if (value := getattr(args, (name := "align"))) and (
            not value <= (limit := (16 if getattr(args, "bits") == 64 else 8))
        ):
            raise InvalidError(
                "Argument",
                value,
                f"{name} should less or equal than {limit}",
            )

    def _set_args(self, args: Namespace) -> None:
        self._memory: str = args.memory
        self._bits: int = args.bits
        self._align: int = args.align
        self._plural: str = args.plural
        self._array: str = args.array
        self._number: str = args.number
        self._prefix: str = args.prefix
        self._postfix: str = args.postfix
        self._guard: str = args.guard
        self._annotation: bool = args.annotation
        self._debug: bool = args.debug

    def __init__(self, args: Namespace) -> None:
        self._invalid_args(args)
        self._set_args(args)

    def __str__(self) -> str:
        return Str.from_rows(
            [
                [name, str(getattr(self, name))]
                for name in MemConfig._rules.keys()
                if not (
                    isinstance(getattr(self, name), str) and not getattr(self, name)
                )
            ],
            separator=" : ",
        ).contents

    @property
    def memory(self) -> str:
        return self._memory

    @property
    def bits(self) -> int:
        return self._bits

    @property
    def align(self) -> int:
        return self._align

    @property
    def plural(self) -> str:
        return self._plural

    @property
    def array(self) -> str:
        return self._array

    @property
    def number(self) -> str:
        return self._number

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def postfix(self) -> str:
        return self._postfix

    @property
    def guard(self) -> str:
        return self._guard

    @property
    def annotation(self) -> bool:
        return self._annotation

    @property
    def debug(self) -> bool:
        return self._debug
