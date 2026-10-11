"""Cabecera de archivos FIT."""

from __future__ import annotations

from .binary import FitBinaryWriter
from .crc import FitCRC


class FitHeader:
    """Genera la cabecera de un archivo FIT."""

    def write(
        self,
        writer: FitBinaryWriter,
        data_size: int,
    ) -> None:
        """Escribe la cabecera FIT."""
    
        writer.write_uint8(14)          # Header Size
        writer.write_uint8(0x10)        # Protocol Version 1.0
        writer.write_uint16(2195)       # Profile Version 21.42
    
        writer.write_uint32(data_size)
    
        writer.write_bytes(b".FIT")
    
        crc = FitCRC.calculate(
            writer.data
        )
    
        writer.write_uint16(crc)