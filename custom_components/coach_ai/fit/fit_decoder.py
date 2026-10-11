"""Decodificador de campos FIT."""

from __future__ import annotations

import struct

from .definitions import BaseType


class FitDecoder:
    """Convierte bytes FIT en valores."""

    @staticmethod
    def decode(
        raw: bytes,
        base_type: int,
    ):

        if base_type == BaseType.ENUM:
            return raw[0]

        if base_type == BaseType.UINT8:
            return raw[0]

        if base_type == BaseType.SINT8:
            return struct.unpack("<b", raw)[0]

        if base_type == BaseType.UINT16:
            return struct.unpack("<H", raw)[0]

        if base_type == BaseType.SINT16:
            return struct.unpack("<h", raw)[0]

        if base_type == BaseType.UINT32:
            return struct.unpack("<I", raw)[0]

        if base_type == BaseType.SINT32:
            return struct.unpack("<i", raw)[0]

        if base_type == BaseType.FLOAT32:
            return struct.unpack("<f", raw)[0]

        if base_type == BaseType.STRING:
            return raw.rstrip(b"\x00").decode(
                "utf-8",
                errors="ignore",
            )

        return raw.hex(" ")