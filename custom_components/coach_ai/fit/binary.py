"""Escritor binario para archivos FIT."""

from __future__ import annotations

import struct


class FitBinaryWriter:
    """Escribe datos binarios en formato little-endian."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    @property
    def data(self) -> bytes:
        return bytes(self._buffer)

    def write_uint8(self, value: int) -> None:
        self._buffer.extend(struct.pack("<B", value))

    def write_sint8(self, value: int) -> None:
        self._buffer.extend(struct.pack("<b", value))

    def write_uint16(self, value: int) -> None:
        self._buffer.extend(struct.pack("<H", value))

    def write_sint16(self, value: int) -> None:
        self._buffer.extend(struct.pack("<h", value))

    def write_uint32(self, value: int) -> None:
        self._buffer.extend(struct.pack("<I", value))

    def write_sint32(self, value: int) -> None:
        self._buffer.extend(struct.pack("<i", value))

    def write_float32(self, value: float) -> None:
        self._buffer.extend(struct.pack("<f", value))

    def write_bytes(self, value: bytes) -> None:
        self._buffer.extend(value)

    def write_string(self, value: str) -> None:
        self._buffer.extend(value.encode("utf-8"))
        self._buffer.append(0)

    def clear(self) -> None:
        self._buffer.clear()

    def size(self) -> int:
        return len(self._buffer)