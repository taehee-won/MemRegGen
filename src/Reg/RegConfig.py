from typing import Final, Dict, Optional, Type, Tuple
from argparse import Namespace

from inc import InvalidError, NotExistError
from inc import Str


class RegConfig:
    # fmt: off
    _rules: Final[Dict[str, Tuple[Type, Optional[bool], Optional[str]]]] = {
        "name":       (str,  True,  "upper"),
        "register":   (str,  False, "upper"),
        "offset":     (str,  False, "upper"),
        "memory":     (str,  False, "lower"),
        "bits":       (int,  False, None),
        "align":      (int,  False, None),
        "mask":       (str,  False, "upper"),
        "shift":      (str,  False, "upper"),
        "access":     (str,  False, "upper"),
        "reset":      (str,  False, "upper"),
        "raw":        (str,  False, "upper"),
        "value":      (str,  False, "upper"),
        "plural":     (str,  False, "upper"),
        "array":      (str,  False, "lower"),
        "number":     (str,  False, "upper"),
        "guard":      (str,  False, "upper"),
        "notes":      (str,  True,  None),
        "annotation": (bool, None,  None),
        "debug":      (bool, None,  None),
    }
    # fmt: on

    def _invalid_args(self, args: Namespace) -> None:
        for name, value in RegConfig._rules.items():
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
        self._name: str = args.name
        self._register: str = args.register
        self._offset: str = args.offset
        self._memory: str = args.memory
        self._bits: int = args.bits
        self._align: int = args.align
        self._mask: str = args.mask
        self._shift: str = args.shift
        self._access: str = args.access
        self._reset: str = args.reset
        self._raw: str = args.raw
        self._value: str = args.value
        self._plural: str = args.plural
        self._array: str = args.array
        self._number: str = args.number
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
                for name in RegConfig._rules.keys()
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
    def register(self) -> str:
        return self._register

    @property
    def offset(self) -> str:
        return self._offset

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
    def mask(self) -> str:
        return self._mask

    @property
    def shift(self) -> str:
        return self._shift

    @property
    def access(self) -> str:
        return self._access

    @property
    def reset(self) -> str:
        return self._reset

    @property
    def raw(self) -> str:
        return self._raw

    @property
    def value(self) -> str:
        return self._value

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
