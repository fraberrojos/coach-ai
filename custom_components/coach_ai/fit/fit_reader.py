"""Lector binario FIT."""

from __future__ import annotations

import struct


class FitReader:
    """Lee datos binarios FIT."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0

    def read_uint8(self) -> int:
        value = struct.unpack_from("<B", self.data, self.offset)[0]
        self.offset += 1
        return value

    def read_uint16(self) -> int:
        value = struct.unpack_from("<H", self.data, self.offset)[0]
        self.offset += 2
        return value

    def read_uint32(self) -> int:
        value = struct.unpack_from("<I", self.data, self.offset)[0]
        self.offset += 4
        return value

    def read_bytes(self, size: int) -> bytes:
        value = self.data[
            self.offset:self.offset + size
        ]
        self.offset += size
        return value