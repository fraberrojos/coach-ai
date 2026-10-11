"""Cálculo del CRC oficial FIT."""

from __future__ import annotations


class FitCRC:
    """Calcula el CRC de un archivo FIT."""

    _TABLE = (
        0x0000, 0xCC01, 0xD801, 0x1400,
        0xF001, 0x3C00, 0x2800, 0xE401,
        0xA001, 0x6C00, 0x7800, 0xB401,
        0x5000, 0x9C01, 0x8801, 0x4400,
    )

    @classmethod
    def update(cls, crc: int, byte: int) -> int:
        tmp = cls._TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc ^= tmp ^ cls._TABLE[byte & 0xF]

        tmp = cls._TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc ^= tmp ^ cls._TABLE[(byte >> 4) & 0xF]

        return crc & 0xFFFF

    @classmethod
    def calculate(cls, data: bytes) -> int:
        crc = 0

        for byte in data:
            crc = cls.update(crc, byte)

        return crc