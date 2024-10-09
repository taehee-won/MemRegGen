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

from src.Pkt.PktConfig import PktConfig


class _PacketKey(Enum):
    NAME = "name"
    DEFINE = "define"


class _FieldKey(Enum):
    FIELD = "field"
    BITS = "bits"


class _EnumKey(Enum):
    ENUM = "enum"
    VALUE = "value"


class _Key(Enum):
    NAME = "name"
    DEFINE = "define"
    FIELD = "field"
    BITS = "bits"
    ENUM = "enum"
    VALUE = "value"


class _Kind(Enum):
    PACKET = "packet,="
    GROUP = "group,@"
    ATTRIBUTE = "attribute,^"


class PktDef:
    name: str = "Packet Definition"

    def __init__(self, file: ReadFile, _: PktConfig) -> None:
        self._file = file

        self._packets: List[Packet] = []
        self._groups: List[Group] = []
        self._items: List[Union[Packet, Group]] = []

        keys, rows = file.csv_contents

        for key in _Key:
            if key.value not in keys:
                raise NotExistError(
                    "Key",
                    f"{key.value} is not exist for CSV"
                    + f": keys({', '.join(key.value for key in _Key)})",
                )

        rows = [_Row(*[row[keys.index(key.value)] for key in _Key]) for row in rows]

        packet = None
        field = None

        for row in rows:
            item = {
                _Kind.PACKET: self._packet,
                _Kind.GROUP: self._group,
                _Kind.ATTRIBUTE: self._attribute,
            }[row.kind](row, packet, field)

            if isinstance(item, Packet):
                packet = item
                field = None

            elif isinstance(item, _Field):
                field = item

    def print(self) -> None:
        rows = []
        rows.append(
            [
                "|",
                "Group",
                "|",
                "Packet",
                "|",
                "Fields",
                "|",
            ]
        )

        for item in self.items:
            if isinstance(item, Packet):
                rows.append(
                    [
                        "|",
                        "",
                        "|",
                        f"{item.name}",
                        "|",
                        ", ".join(
                            f"{field.name}"
                            + (
                                f"({', '.join(enum.name for enum in field.enums)})"
                                if field.enums
                                else ""
                            )
                            for field in item.fields
                        ),
                        "|",
                    ]
                )

            elif isinstance(item, Group):
                for packet in item.packets:
                    rows.append(
                        [
                            "|",
                            item.name,
                            "|",
                            f"{packet.name}",
                            "|",
                            ", ".join(
                                f"{field.name}"
                                + (
                                    f"({', '.join(enum.name for enum in field.enums)})"
                                    if field.enums
                                    else ""
                                )
                                for field in packet.fields
                            ),
                            "|",
                        ]
                    )

        print(
            Str.from_rows(rows)
            .insert_guard(".")
            .insert_line("PktDef - Group, Packet")
            .add_guard("-")
        )

    @property
    def file(self) -> ReadFile:
        return self._file

    @property
    def items(self) -> List[Union["Packet", "Group"]]:
        return self._items

    def _packet(
        self,
        row: "_Row",
        packet: Optional["Packet"],
        field: Optional["_Field"],
    ) -> "Packet":
        if row.name in [packet.name for packet in self._packets]:
            raise DuplicatedError("Name", row.name)

        packet_ = Packet(row.name)

        self._packets.append(packet_)
        self._items.append(packet_)

        return packet_

    def _group(
        self,
        row: "_Row",
        packet: Optional["Packet"],
        field: Optional["_Field"],
    ) -> "Packet":
        tokens = row.define.split(",")
        if len(tokens) != 2:
            raise InvalidError(
                "Define",
                row.define,
                f"invalid number of tokens in define: expected 2",
            )

        if (name := row.name + "_" + tokens[1]) in [
            packet.name for packet in self._packets
        ]:
            raise DuplicatedError("Name", name)

        packet = Packet(tokens[1])

        self._packets.append(packet)

        for group in self._groups:
            if group.name == row.name:
                group.append(packet)
                break

        else:
            group = Group(row.name)
            group.append(packet)
            self._groups.append(group)
            self._items.append(group)

        return packet

    def _attribute(
        self,
        row: "_Row",
        packet: Optional["Packet"],
        field: Optional["_Field"],
    ) -> Optional["_Field"]:
        if row.field is not None:
            field = self._field(row, packet, field)

        if row.enum is not None:
            self._enum(row, packet, field)

        return field

    def _field(
        self,
        row: "_Row",
        packet: Optional["Packet"],
        field: Optional["_Field"],
    ) -> "_Field":
        if packet is None:
            raise NotExistError(
                "Packet",
                f"{row.field} can not be registered as attribute",
            )

        if row.field is None:
            raise NotExpectedError("Not Exist, Field: field should never be none")

        if any(field.name == row.field for field in packet.fields):
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
            for field in packet.fields
        ):
            raise DuplicatedError("Bits", row.bits)

        field_ = _Field(row.field, bits)

        packet.append(field_)

        return field_

    def _enum(
        self,
        row: "_Row",
        packet: Optional["Packet"],
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

        if not (IntStr.is_IntStr(row.value) or HexStr.is_HexStr(row.value)):
            raise InvalidError(
                "Value",
                row.value,
                f"enum value should be integer or hexadecimal",
            )

        enum = _Enum(row.enum, row.value)

        if any(e.value.value == enum.value.value for e in field.enums):
            raise DuplicatedError(
                "Value",
                enum.value,
                f"field({field.name}) has duplicated values",
            )

        field.append(enum)


class _Row:
    def __init__(
        self,
        name: str,
        define: str,
        field: str,
        bits: str,
        enum: str,
        value: str,
    ) -> None:
        for n in [name, field, enum]:
            if n and (
                n in ["int", "float", "while", "if", "else", "return"]
                or (not bool(match(r"^[A-Za-z_][A-Za-z0-9_]*$", n)))
            ):
                raise InvalidError("Name", n)

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
        self._define = define
        self._field = field if field else None
        self._bits = bits if bits else None
        self._enum = enum if enum else None
        self._value = value if value else None

        if kind == _Kind.PACKET or kind == _Kind.GROUP:
            for key in _PacketKey:
                if not getattr(self, f"_{key.value}"):
                    raise InvalidError(
                        "CSV Row",
                        ",".join([name, define, field, bits, enum, value]),
                        "all cell of defined keys for packet or group should be exist"
                        + f": keys({', '.join(key.value for key in _PacketKey)})",
                    )

        elif kind == _Kind.ATTRIBUTE:
            if any(
                getattr(self, f"_{key.value}", None) is not None for key in _FieldKey
            ):
                for key in _FieldKey:
                    if not getattr(self, f"_{key.value}"):
                        raise InvalidError(
                            "CSV Row",
                            ",".join([name, define, field, bits, enum, value]),
                            "all cell of defined keys for field should be exist"
                            + f": keys({', '.join(key.value for key in _FieldKey)})",
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

    @property
    def name(self) -> str:
        if self._name is None:
            raise NotExpectedError("Not Exist, Name: name should never be none")

        return self._name

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
    def enum(self) -> Optional[str]:
        return self._enum

    @property
    def value(self) -> str:
        if self._value is None:
            raise NotExpectedError("Not Exist, Value: value should never be none")

        return self._value

    @property
    def kind(self) -> _Kind:
        if self._kind is None:
            raise NotExpectedError("Not Exist, Kind: kind should never be none")

        return self._kind


class Packet:
    def __init__(self, name: str) -> None:
        self._name: str = name

        self._fields: List[_Field] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def fields(self) -> List["_Field"]:
        return self._fields

    def append(self, field: "_Field") -> None:
        self._fields.append(field)
        self._fields.sort()


class Group:
    def __init__(self, name: str) -> None:
        self._name: str = name

        self._packets: List[Packet] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def packets(self) -> List["Packet"]:
        return self._packets

    def append(self, packet: Packet) -> None:
        self._packets.append(packet)


class _Field:
    def __init__(self, name: str, bits: Tuple[int, int]) -> None:
        self._name: str = name
        self._bits: Tuple[int, int] = bits

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
    def enums(self) -> List["_Enum"]:
        return self._enums

    def append(self, enum: "_Enum") -> None:
        self._enums.append(enum)
        self._enums.sort()


class _Enum:
    def __init__(self, name: str, value: str) -> None:
        self._name: str = name
        self._value: Union[IntStr, HexStr] = (
            IntStr(value) if IntStr.is_IntStr(value) else HexStr(value)
        )

    def __lt__(self, other: "_Enum") -> bool:
        return self.value.value < other.value.value

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> Union[IntStr, HexStr]:
        return self._value
