from typing import List, Union, Optional, Tuple
from enum import Enum
from re import match

from inc import (
    InvalidCSVRowError,
    NotExistCSVKeyError,
    InvalidKindError,
    NotExpectedError,
    DuplicatedNameError,
    InvalidNameError,
    InvalidDefineError,
    NotExistAliasError,
    NotExistBookmarkError,
)
from inc import ReadFile, Str, HexStr, IntStr

from src.Mem.MemConfig import MemConfig


class _Key(Enum):
    NAME = "name"
    VALUE = "value"
    DEFINE = "define"


class _Kind(Enum):
    ADDRESS = "address,="
    ARRAY = "array,*"
    ALIAS = "alias,~"
    BOOKMARK = "bookmark,#"


class MemDef:
    name: str = "Memory Definition"

    def __init__(self, file: ReadFile, _: MemConfig) -> None:
        self._file = file

        self._addresses: List[Address] = []
        self._arrays: List[Array] = []
        self._aliases: List[Alias] = []
        self._bookmarks: List[Bookmark] = []

        keys, rows = file.csv_contents

        for row in rows:
            if not all(cell for cell in row):
                raise InvalidCSVRowError(row, "all cell should be exist")

        for key in _Key:
            if key.value not in keys:
                raise NotExistCSVKeyError(key.value)

        rows = [_Row(*[row[keys.index(key.value)] for key in _Key]) for row in rows]

        for kind, add in {
            _Kind.ADDRESS: self._address,
            _Kind.ARRAY: self._array,
            _Kind.ALIAS: self._alias,
            _Kind.BOOKMARK: self._bookmark,
        }.items():
            for row in rows:
                if row.kind == kind:
                    add(row)

        self._addresses = sorted(self._addresses)
        self._arrays = sorted(self._arrays)

    @property
    def debug_str(self) -> str:
        return "\n".join(
            [
                Str.from_rows(
                    [[address.name, address.address] for address in self._addresses],
                    ": ",
                )
                .insert_guard("-")
                .insert_line("MemDef - Address")
                .add_guard("=")
                .contents,
                Str.from_rows(
                    [
                        [array.name, address.name, address.address]
                        for array in self._arrays
                        for address in array.addresses
                    ],
                    ": ",
                )
                .insert_guard("-")
                .insert_line("MemDef - Array")
                .add_guard("=")
                .contents,
                Str.from_rows(
                    [[alias.name, alias.alias.name] for alias in self._aliases], ": "
                )
                .insert_guard("-")
                .insert_line("MemDef - Alias")
                .add_guard("=")
                .contents,
                Str.from_rows(
                    [
                        [bookmark.name, bookmark.bookmark]
                        for bookmark in self._bookmarks
                    ],
                    ": ",
                )
                .insert_guard("-")
                .insert_line("MemDef - Bookmark")
                .add_guard("=")
                .contents,
            ]
        )

    @property
    def file(self) -> ReadFile:
        return self._file

    @property
    def addresses(self) -> List["Address"]:
        return self._addresses

    @property
    def arrays(self) -> List["Array"]:
        return self._arrays

    @property
    def aliases(self) -> List["Alias"]:
        return self._aliases

    @property
    def bookmarks(self) -> List["Bookmark"]:
        return self._bookmarks

    def _address(self, row: "_Row") -> None:
        if row.name in [address.name for address in self._addresses]:
            raise DuplicatedNameError(row.name)

        self._addresses.append(Address(row.name, row.value))

    def _array(self, row: "_Row") -> None:
        if row.name in [address.name for address in self._addresses]:
            raise DuplicatedNameError(row.name)

        tokens = row.define.split(",")
        if len(tokens) != 4:
            raise InvalidDefineError(
                row.define,
                f"invalid number of tokens in define" + f": expected 4",
            )

        start = IntStr(tokens[1])
        count = IntStr(tokens[2])
        step = HexStr(tokens[3])

        address = HexStr(row.value)
        array_addresses = [
            Address(
                f"{row.name}_{index}",
                f"0x{(int(address, 16) + (int(step, 16) * (index - int(start)))):X}",
            )
            for index in range(int(start), int(start) + int(count))
        ]

        for address in array_addresses:
            if address.name in (
                [address.name for address in self._addresses]
                + [
                    address.name
                    for array in self._arrays
                    for address in array.addresses
                ]
            ):
                raise DuplicatedNameError(address.name)

        for array in self._arrays:
            if array.name == row.name:
                array.extend(array_addresses)
                break

        else:
            self._arrays.append(Array(row.name, array_addresses))

    def _alias(self, row: "_Row") -> None:
        if row.name in (
            [address.name for address in self._addresses]
            + [array.name for array in self._arrays]
            + [address.name for array in self._arrays for address in array.addresses]
        ):
            raise DuplicatedNameError(row.name)

        for address in self._addresses:
            if row.value == address.name:
                self._aliases.append(Alias(row.name, address))
                return

        for array in self._arrays:
            if row.value == array.name:
                self._aliases.append(Alias(row.name, array))
                return

            for address in array.addresses:
                if row.value == address.name:
                    self._aliases.append(Alias(row.name, address))
                    return

        raise NotExistAliasError(row.value)

    def _bookmark(self, row: "_Row") -> None:
        for address in self._addresses:
            if row.value == address.name:
                self._bookmarks.append(Bookmark(row.name, row.value))
                return

        for array in self._arrays:
            if row.value == array.name:
                self._bookmarks.append(Bookmark(row.name, row.value))
                return

            for address in array.addresses:
                if row.value == address.name:
                    self._bookmarks.append(Bookmark(row.name, row.value))
                    return

        raise NotExistBookmarkError(row.value)


class _Row:
    def __init__(self, name: str, value: str, define: str) -> None:
        if name in ["int", "float", "while", "if", "else", "return"] or (
            not bool(match(r"^[A-Za-z_][A-Za-z0-9_]*$", name))
        ):
            raise InvalidNameError(name)

        if (
            kind := next(
                (
                    kind
                    for kind in _Kind
                    if (defined_kind := define.split(",")[0])
                    in kind.value.strip().split(",")
                ),
                None,
            )
        ) is None:
            raise InvalidKindError(
                defined_kind,
                f"name({name}), value({value}), define({define})"
                + f": kind should be one of these types"
                + f": {', '.join({token for kind in _Kind for token in kind.value.strip().split(',')})}",
            )

        self._name = name
        self._value = value
        self._define = define
        self._kind = kind

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> str:
        return self._value

    @property
    def define(self) -> str:
        return self._define

    @property
    def kind(self) -> _Kind:
        if self._kind is None:
            raise NotExpectedError("Not Exist, Kind: kind should never be none")

        return self._kind


class Address:
    def __init__(self, name: str, address: str) -> None:
        self._name: str = name
        self._address: HexStr = HexStr(address)

    def __lt__(self, other: "Address") -> bool:
        return self._address.value < other.address.value

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> HexStr:
        return self._address


class Array:
    def __init__(self, name: str, addresses: List[Address]) -> None:
        self._name = name
        self._addresses = sorted(addresses)

    def __lt__(self, other: "Array") -> bool:
        return self.addresses[0].address.value < other.addresses[0].address.value

    @property
    def name(self) -> str:
        return self._name

    @property
    def addresses(self) -> List[Address]:
        return self._addresses

    @property
    def indexes(self) -> List[int]:
        return [self.get_index(address.name) for address in self._addresses]

    @property
    def step_shift(self) -> Optional[Tuple[HexStr, int]]:
        if len(self.addresses) == 0:
            return None

        if len(self.addresses) == 1:
            return self.addresses[0].address, 0

        start_index = self.get_index(self.addresses[0].name)
        start_address = self.addresses[0].address.value

        step = (self.addresses[1].address.value - start_address) / (
            self.get_index(self.addresses[1].name) - start_index
        )

        if not step.is_integer() or step <= 0:
            return None

        step = int(step)

        if (step & (step - 1)) != 0:
            return None

        base = start_address - (step * start_index)

        if any(
            base != (address.address.value - (step * self.get_index(address.name)))
            for address in self.addresses
        ):
            return None

        return HexStr.from_int(base), step.bit_length()

    def extend(self, addresses: List[Address]):
        self.addresses.extend(addresses)
        self.addresses.sort()

    @staticmethod
    def get_index(name: str) -> int:
        index = name.split("_")[-1]
        if not index.isdigit():
            raise NotExpectedError(
                f"Invalid, Index({index}): array address({name}) should be valid index"
            )

        return int(index)


class Alias:
    def __init__(self, name: str, alias: Union[Address, Array]) -> None:
        self._name = name
        self._alias = alias

    @property
    def name(self) -> str:
        return self._name

    @property
    def alias(self) -> Union[Address, Array]:
        return self._alias


class Bookmark:
    def __init__(self, name: str, bookmark: str) -> None:
        self._name = name
        self._bookmark = bookmark

    @property
    def name(self) -> str:
        return self._name

    @property
    def bookmark(self) -> str:
        return self._bookmark
