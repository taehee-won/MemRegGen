from typing import List, Union, Optional, Tuple
from enum import Enum
from re import match

from inc import (
    InvalidError,
    DuplicatedError,
    NotExistError,
    NotExpectedError,
)
from inc import ReadFile, Str, HexStr, IntStr

from src.Reg.RegConfig import RegConfig


class _OffsetKey(Enum):
    NAME = "name"
    VALUE = "value"
    DEFINE = "define"


class _FieldKey(Enum):
    FIELD = "field"
    BITS = "bits"
    ACCESS = "access"
    RESET = "reset"


class _EnumKey(Enum):
    ENUM = "enum"
    VAL = "val"


class _Key(Enum):
    NAME = "name"
    VALUE = "value"
    DEFINE = "define"
    FIELD = "field"
    BITS = "bits"
    ACCESS = "access"
    RESET = "reset"
    ENUM = "enum"
    VAL = "val"


class _Kind(Enum):
    OFFSET = "offset,="
    ARRAY = "array,*"
    GROUP = "group,@"
    ATTRIBUTE = "attribute,^"


class _Opt(Enum):
    Bit32 = "-32"
    Bit64 = "-64"


class RegDef:
    name: str = "Register Definition"

    def __init__(self, file: ReadFile, _: RegConfig) -> None:
        self._file = file

        self._offsets: List[Offset] = []
        self._arrays: List[Array] = []

        keys, rows = file.csv_contents

        for key in _Key:
            if key.value not in keys:
                raise NotExistError(
                    "Key",
                    f"{key.value} is not exist for CSV"
                    + f": keys({', '.join(key.value for key in _Key)})",
                )

        rows = [_Row(*[row[keys.index(key.value)] for key in _Key]) for row in rows]

        offset = None
        field = None

        for row in rows:
            item = {
                _Kind.OFFSET: self._offset,
                _Kind.ARRAY: self._array,
                _Kind.GROUP: self._group,
                _Kind.ATTRIBUTE: self._attribute,
            }[row.kind](row, offset, field)

            if isinstance(item, Offset):
                offset = item
                field = None

            elif isinstance(item, _Field):
                field = item

        self._offsets = sorted(self._offsets)
        self._arrays = sorted(self._arrays)

    def print(self) -> None:
        print(
            "\n".join(
                [
                    str(
                        Str.from_rows(
                            [
                                [
                                    offset.name,
                                    "|",
                                    offset.offset,
                                    "|",
                                    ", ".join(
                                        field.name
                                        + (
                                            f"({', '.join(enum.name for enum in field.enums)})"
                                            if field.enums
                                            else ""
                                        )
                                        for field in offset.fields
                                    ),
                                ]
                                for offset in self._offsets
                            ]
                        )
                        .insert_guard(".")
                        .insert_line("RegDef - Offset")
                        .add_guard("-")
                    ),
                    str(
                        Str.from_rows(
                            [
                                [
                                    offset.name,
                                    "|",
                                    offset.offset,
                                    "|",
                                    ", ".join(
                                        field.name
                                        + (
                                            f"({', '.join(enum.name for enum in field.enums)})"
                                            if field.enums
                                            else ""
                                        )
                                        for field in group.fields
                                    ),
                                ]
                                for offset, group in [
                                    (
                                        Offset(
                                            f"{array.name}_{offset.name}_{group.name}",
                                            HexStr.from_int(
                                                offset.offset.value + group.offset.value
                                            ),
                                        ),
                                        group,
                                    )
                                    for array in self._arrays
                                    for offset in array.offsets
                                    for group in array.groups
                                ]
                            ]
                        )
                        .insert_guard(".")
                        .insert_line("RegDef - Array")
                        .add_guard("-")
                    ),
                ]
            )
        )

    @property
    def file(self) -> ReadFile:
        return self._file

    @property
    def offsets(self) -> List["Offset"]:
        return self._offsets

    @property
    def arrays(self) -> List["Array"]:
        return self._arrays

    def _offset(
        self,
        row: "_Row",
        _: Optional["Offset"],
        field: Optional["_Field"],
    ) -> "Offset":
        if row.name in [offset.name for offset in self._offsets]:
            raise DuplicatedError("Name", row.name)

        offset = Offset(row.name, row.value, row.opts)

        self._offsets.append(offset)

        return offset

    def _array(
        self,
        row: "_Row",
        _: Optional["Offset"],
        field: Optional["_Field"],
    ) -> None:
        for array in self._arrays:
            if array.name == row.name:
                break

        else:
            array = Array(row.name)

            self._arrays.append(array)

        tokens = row.define.split(",")
        if len(tokens) != 3 and len(tokens) != 4:
            raise InvalidError(
                "Define",
                row.define,
                f"invalid number of tokens in define: expected 3 or 4",
            )

        start = IntStr(tokens[1])
        count = IntStr(tokens[2])
        step = HexStr(tokens[3]) if len(tokens) == 4 else HexStr.from_int(0)

        if 1 < count.value and step.value == 0:
            raise InvalidError(
                "Define",
                row.define,
                f"invalid count and step combination"
                + f": step is zero, but count({count}) is greater than 1",
            )

        offset = HexStr(row.value)
        array_offsets = [
            Offset(
                str(index),
                f"0x{(int(offset, 16) + (int(step, 16) * (index - int(start)))):X}",
                row.opts,
            )
            for index in range(int(start), int(start) + int(count))
        ]

        for offset in array_offsets:
            if f"{array.name}_{offset.name}" in (
                [offset_.name for offset_ in self._offsets]
                + [
                    f"{array_.name}_{offset_.name}"
                    for array_ in self._arrays
                    for offset_ in array_.offsets
                ]
            ):
                raise DuplicatedError("Name", offset.name)

        for offset in array_offsets:
            array.append_offset(offset)

    def _group(
        self,
        row: "_Row",
        _: Optional["Offset"],
        field: Optional["_Field"],
    ) -> "Offset":
        tokens = row.define.split(",")
        if len(tokens) != 2:
            raise InvalidError(
                "Define",
                row.define,
                f"invalid number of tokens in define: expected 2",
            )

        array_name = tokens[1]
        for array in self._arrays:
            if array.name == array_name:
                break

        else:
            raise DuplicatedError("Name", tokens[1])

        if row.name in [group.name for group in array._groups]:
            raise DuplicatedError("Name", row.name)

        offset = Offset(row.name, row.value, row.opts)

        array.append_group(offset)

        return offset

    def _attribute(
        self,
        row: "_Row",
        offset: Optional["Offset"],
        field: Optional["_Field"],
    ) -> Optional["_Field"]:
        if row.field is not None:
            field = self._field(row, offset, field)

        if row.enum is not None:
            self._enum(row, offset, field)

        return field

    def _field(
        self,
        row: "_Row",
        offset: Optional["Offset"],
        field: Optional["_Field"],
    ) -> "_Field":
        if offset is None:
            raise NotExistError(
                "Offset",
                f"{row.field} can not be registered as attribute",
            )

        if row.field is None:
            raise NotExpectedError("Not Exist, Field: field should never be none")

        if any(field.name == row.field for field in offset.fields):
            raise DuplicatedError("Field", row.field)

        if len(row.bits) <= 2 or row.bits[0] != "[" or row.bits[-1] != "]":
            raise InvalidError(
                "Bits",
                row.bits,
                "bits should fit the format [XX] or [XX:XX]",
            )

        bits = row.bits[1:-1]
        tokens = bits.split(":")

        if any(not token.isdigit() for token in tokens):
            raise InvalidError("Bits", row.bits, "token of bits should be number")

        if len(tokens) == 0 or 2 < len(tokens):
            raise InvalidError(
                "Bits",
                row.bits,
                "bits should fit the format [XX] or [XX:XX]",
            )

        bits = (
            (int(tokens[0]), int(tokens[0]))
            if len(tokens) == 1
            else (
                (int(tokens[1]), int(tokens[0]))
                if int(tokens[1]) > int(tokens[0])
                else (int(tokens[0]), int(tokens[1]))
            )
        )

        if any(bit < 0 or bit > 31 for bit in bits):
            raise InvalidError("Bits", row.bits, "token of bits should be in 0 to 31")

        if any(
            field.bits[0] >= bits[0] >= field.bits[1]
            or field.bits[0] >= bits[1] >= field.bits[1]
            for field in offset.fields
        ):
            raise DuplicatedError("Bits", row.bits)

        field_ = _Field(row.field, bits, row.access, row.reset)

        offset.append(field_)

        return field_

    def _enum(
        self,
        row: "_Row",
        offset: Optional["Offset"],
        field: Optional["_Field"],
    ) -> None:
        if field is None:
            raise NotExistError(
                "Field",
                f"{row.enum} can not be registered as attribute",
            )

        if row.enum is None:
            raise NotExpectedError("Not Exist, Enum: enum should never be none")

        if any(enum.name == row.enum for enum in field.enums):
            raise DuplicatedError("Enum", row.enum)

        if not (IntStr.is_IntStr(row.val) or HexStr.is_HexStr(row.val)):
            raise InvalidError(
                "Val",
                row.val,
                f"enum val should be integer or hexadecimal",
            )

        enum = _Enum(row.enum, row.val)

        if any(e.val.value == enum.val.value for e in field.enums):
            raise DuplicatedError(
                "Val",
                enum.val,
                f"field({field.name}) has duplicated vals",
            )

        field.append(enum)


class _Row:
    def __init__(
        self,
        name: str,
        value: str,
        define: str,
        field: str,
        bits: str,
        access: str,
        reset: str,
        enum: str,
        val: str,
    ) -> None:
        for n in [name, field, enum]:
            if n and (
                n in ["int", "float", "while", "if", "else", "return"]
                or (not bool(match(r"^[A-Za-z_][A-Za-z0-9_]*$", n)))
            ):
                raise InvalidError("Name", n)

        opts = define.split(" ")[1:]
        define = define.split(" ")[0]

        kind = next(
            (
                kind
                for kind in _Kind
                if (defined_kind := define.split(",")[0])
                in kind.value.strip().split(",")
            ),
            None,
        )
        if kind is None:
            raise InvalidError(
                "Kind",
                defined_kind,
                f"name({name}), define({define})"
                + f": kind should be one of these types"
                + f": {', '.join({token for kind in _Kind for token in kind.value.strip().split(',')})}",
            )

        self._name = name if name else None
        self._value = value if value else None
        self._define = define
        self._field = field if field else None
        self._bits = bits if bits else None
        self._access = access if access else None
        self._reset = reset if reset else None
        self._enum = enum if enum else None
        self._val = val if val else None

        if kind == _Kind.OFFSET or kind == _Kind.ARRAY or kind == _Kind.GROUP:
            for key in _OffsetKey:
                if not getattr(self, f"_{key.value}"):
                    raise InvalidError(
                        "CSV Row",
                        ",".join([name, define, field, bits, enum, value]),
                        "all cell of defined keys for offset or array or group should be exist"
                        + f": keys({', '.join(key.value for key in _OffsetKey)})",
                    )

        elif kind == _Kind.ATTRIBUTE:
            field_keys = ["field", "bits"]  # access, reset is optional
            if any(getattr(self, f"_{key}", None) is not None for key in field_keys):
                for key in field_keys:
                    if not getattr(self, f"_{key}"):
                        raise InvalidError(
                            "CSV Row",
                            ",".join([name, define, field, bits, enum, value]),
                            "all cell of defined keys for field should be exist"
                            + f": keys({', '.join(key for key in field_keys)})",
                        )

            if any(
                getattr(self, f"_{key.value}", None) is not None for key in _EnumKey
            ):
                for key in _EnumKey:
                    if not getattr(self, f"_{key.value}"):
                        raise InvalidError(
                            "CSV Row",
                            ",".join([name, define, field, bits, enum, value]),
                            "all cell of defined keys for enum should be exist"
                            + f": keys({', '.join(key.value for key in _EnumKey)})",
                        )

        self._kind = kind

        for opt in opts:
            if opt not in [_opt.value for _opt in _Opt]:
                raise InvalidError(
                    "opt", opt, f"opts({', '.join(_opt.value for _opt in _Opt)})"
                )

        self._opts = [_Opt(opt) for opt in opts]

    @property
    def name(self) -> str:
        if self._name is None:
            raise NotExpectedError("Not Exist, Name: name should never be none")

        return self._name

    @property
    def value(self) -> str:
        if self._value is None:
            raise NotExpectedError("Not Exist, Value: value should never be none")

        return self._value

    @property
    def define(self) -> str:
        return self._define

    @property
    def field(self) -> Optional[str]:
        return self._field

    @property
    def bits(self) -> str:
        if self._bits is None:
            raise NotExpectedError("Not Exist, Bits: bits should never be none")

        return self._bits

    @property
    def access(self) -> Optional[str]:
        return self._access

    @property
    def reset(self) -> Optional[str]:
        return self._reset

    @property
    def enum(self) -> Optional[str]:
        return self._enum

    @property
    def val(self) -> str:
        if self._val is None:
            raise NotExpectedError("Not Exist, Val: val should never be none")

        return self._val

    @property
    def opts(self) -> List[_Opt]:
        return self._opts

    @property
    def kind(self) -> _Kind:
        if self._kind is None:
            raise NotExpectedError("Not Exist, Kind: kind should never be none")

        return self._kind


class Offset:
    def __init__(self, name: str, offset: str, opts: List[_Opt] = []) -> None:
        self._name: str = name
        self._offset: HexStr = HexStr(offset)
        self._opts: List[_Opt] = opts

        self._fields: List[_Field] = []

    def __lt__(self, other: "Offset") -> bool:
        return self._offset.value < other.offset.value

    @property
    def name(self) -> str:
        return self._name

    @property
    def offset(self) -> HexStr:
        return self._offset

    @property
    def opts(self) -> List[_Opt]:
        return self._opts

    @property
    def fields(self) -> List["_Field"]:
        return self._fields

    def append(self, field: "_Field") -> None:
        self._fields.append(field)
        self._fields.sort()


class Array:
    def __init__(
        self,
        name: str,
        offsets: List[Offset] = [],
        groups: List[Offset] = [],
    ) -> None:
        self._name: str = name
        self._offsets: List[Offset] = offsets
        self._groups: List[Offset] = groups

    def __lt__(self, other: "Array") -> bool:
        return (len(self._offsets) == 0 and len(other.offsets) != 0) or (
            len(self._offsets) != 0
            and len(other.offsets) != 0
            and self._offsets[0] < other.offsets[0]
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def offsets(self) -> List[Offset]:
        return self._offsets

    @property
    def indexes(self) -> List[int]:
        return [int(offset.name) for offset in self._offsets]

    @property
    def step(self) -> Optional[Tuple[HexStr, Optional[HexStr], Optional[int]]]:
        if len(self._offsets) == 0:
            return None

        if len(self._offsets) == 1:
            return self._offsets[0].offset, None, None

        start_index = int(self._offsets[0].name)
        start_offset = self._offsets[0].offset.value

        step = (self._offsets[1].offset.value - start_offset) / (
            int(self._offsets[1].name) - start_index
        )

        if not step.is_integer() or step <= 0:
            return None

        step = int(step)
        base = start_offset - (step * start_index)

        if any(
            base != (offset.offset.value - (step * int(offset.name)))
            for offset in self._offsets
        ):
            return None

        return (
            (HexStr.from_int(base), HexStr.from_int(step), step.bit_length() - 1)
            if (step & (step - 1)) == 0
            else (HexStr.from_int(base), HexStr.from_int(step), None)
        )

    @property
    def groups(self) -> List[Offset]:
        return self._groups

    def append_offset(self, offset: Offset) -> None:
        self._offsets.append(offset)
        self._offsets.sort()

    def append_group(self, group: Offset) -> None:
        self._groups.append(group)
        self._groups.sort()


class _Field:
    def __init__(
        self,
        name: str,
        bits: Tuple[int, int],
        access: Optional[str],
        reset: Optional[str],
    ) -> None:
        self._name: str = name
        self._bits: Tuple[int, int] = bits
        self._access: Optional[str] = access
        self._reset: Optional[Union[IntStr, HexStr]] = (
            (IntStr(reset) if IntStr.is_IntStr(reset) else HexStr(reset))
            if reset is not None
            else None
        )

        self._enums: List[_Enum] = []

    def __lt__(self, other: "_Field") -> bool:
        return self.bits[1] < other.bits[1]

    @property
    def name(self) -> str:
        return self._name

    @property
    def bits(self) -> Tuple[int, int]:
        return self._bits

    @property
    def access(self) -> Optional[str]:
        return self._access

    @property
    def reset(self) -> Optional[Union[IntStr, HexStr]]:
        return self._reset

    @property
    def enums(self) -> List["_Enum"]:
        return self._enums

    def append(self, enum: "_Enum") -> None:
        self._enums.append(enum)
        self._enums.sort()


class _Enum:
    def __init__(self, name: str, val: str) -> None:
        self._name: str = name
        self._val: Union[IntStr, HexStr] = (
            IntStr(val) if IntStr.is_IntStr(val) else HexStr(val)
        )

    def __lt__(self, other: "_Enum") -> bool:
        return self.val.value < other.val.value

    @property
    def name(self) -> str:
        return self._name

    @property
    def val(self) -> Union[IntStr, HexStr]:
        return self._val
