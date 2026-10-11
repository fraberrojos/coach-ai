"""Inspector de archivos FIT."""

from __future__ import annotations

import logging
import struct

from .fit_reader import FitReader


_LOGGER = logging.getLogger(__name__)


class FitParser:
    """Inspecciona definiciones y mensajes de datos FIT."""

    BASE_TYPES = {
        0x00: "ENUM",
        0x01: "SINT8",
        0x02: "UINT8",
        0x83: "SINT16",
        0x84: "UINT16",
        0x85: "SINT32",
        0x86: "UINT32",
        0x07: "STRING",
        0x88: "FLOAT32",
        0x89: "FLOAT64",
        0x0A: "UINT8Z",
        0x8B: "UINT16Z",
        0x8C: "UINT32Z",
        0x0D: "BYTE",
    }

    MESSAGE_NAMES = {
        0: "FILE_ID",
        26: "WORKOUT",
        27: "WORKOUT_STEP",
        49: "FILE_CREATOR",
    }

    def __init__(self, data: bytes) -> None:
        self.reader = FitReader(data)
        self.definitions: dict[int, dict] = {}
        self.data_end = 0

    def parse(self) -> None:
        """Parsea el FIT completo."""
    
        self._parse_header()
    
        while self.reader.offset < self.data_end:
    
            remaining = self.data_end - self.reader.offset
    
            if remaining < 1:
                break
    
            self._parse_record()
    
        diagnostic = (
            "===== FIN FIT =====\n"
            f"offset={self.reader.offset}\n"
            f"data_end={self.data_end}\n"
            f"file_size={len(self.reader.data)}\n"
        )
    
        _LOGGER.debug(diagnostic)
    
        try:
            with open(
                "/config/fit_debug.txt",
                "a",
                encoding="utf-8",
            ) as file:
                file.write("\n" + diagnostic)
    
        except OSError as err:
            _LOGGER.debug(
                "No se pudo escribir fit_debug.txt: %s",
                err,
            )

    def _parse_header(self) -> None:
        """Lee la cabecera FIT."""

        header_size = self.reader.read_uint8()
        protocol = self.reader.read_uint8()
        profile = self.reader.read_uint16()
        data_size = self.reader.read_uint32()
        signature = self.reader.read_bytes(4)

        # Cabecera estándar de 14 bytes.
        header_crc = None

        if header_size >= 14:
            header_crc = self.reader.read_uint16()

        # Si alguna vez encontramos una cabecera mayor,
        # saltamos los bytes adicionales.
        extra = header_size - self.reader.offset

        if extra > 0:
            self.reader.read_bytes(extra)

        self.data_end = header_size + data_size

        _LOGGER.debug("========================================")
        _LOGGER.debug("FIT HEADER")
        _LOGGER.debug("Header size : %d", header_size)
        _LOGGER.debug("Protocol    : %d", protocol)
        _LOGGER.debug("Profile     : %d", profile)
        _LOGGER.debug("Data size   : %d", data_size)
        _LOGGER.debug("Signature   : %r", signature)
        _LOGGER.debug("Header CRC  : %s", header_crc)
        _LOGGER.debug("Data end    : %d", self.data_end)
        _LOGGER.debug("========================================")

    def _parse_record(self) -> None:
        """Lee un registro FIT."""

        header = self.reader.read_uint8()

        # Por ahora esperamos headers normales.
        # Si aparece compressed timestamp, lo indicamos claramente.
        if header & 0x80:
            raise RuntimeError(
                f"Compressed timestamp header no soportado: 0x{header:02X}"
            )

        is_definition = bool(header & 0x40)
        local_message = header & 0x0F

        if is_definition:
            self._parse_definition(local_message)
        else:
            self._parse_message(local_message)

    def _parse_definition(self, local_message: int) -> None:
        """Lee un Definition Message."""

        self.reader.read_uint8()  # reserved
        architecture = self.reader.read_uint8()

        if architecture == 0:
            global_message = self.reader.read_uint16()
        else:
            raw = self.reader.read_bytes(2)
            global_message = struct.unpack(">H", raw)[0]

        field_count = self.reader.read_uint8()

        fields = []

        for _ in range(field_count):
            number = self.reader.read_uint8()
            size = self.reader.read_uint8()
            base_type = self.reader.read_uint8()

            fields.append(
                {
                    "number": number,
                    "size": size,
                    "base_type": base_type,
                }
            )

        self.definitions[local_message] = {
            "global_message": global_message,
            "architecture": architecture,
            "fields": fields,
        }

        name = self.MESSAGE_NAMES.get(
            global_message,
            f"GLOBAL_{global_message}",
        )

        _LOGGER.debug("")
        _LOGGER.debug(
            "===== DEFINITION %s | local=%d global=%d =====",
            name,
            local_message,
            global_message,
        )

        for field in fields:
            _LOGGER.debug(
                "Field=%3d size=%2d type=%s (0x%02X)",
                field["number"],
                field["size"],
                self.BASE_TYPES.get(
                    field["base_type"],
                    "UNKNOWN",
                ),
                field["base_type"],
            )

    def _parse_message(self, local_message: int) -> None:
        """Lee y decodifica un Data Message."""
    
        definition = self.definitions.get(local_message)
    
        if definition is None:
            raise RuntimeError(
                f"No existe definición para local_message={local_message}"
            )
    
        global_message = definition["global_message"]
    
        name = self.MESSAGE_NAMES.get(
            global_message,
            f"GLOBAL_{global_message}",
        )
    
        message_size = sum(
            field["size"]
            for field in definition["fields"]
        )
    
        remaining = self.data_end - self.reader.offset
    
        if message_size > remaining:
            _LOGGER.error(
                "MENSAJE FIT SOBREPASA DATA_END | "
                "local=%d global=%d (%s) | "
                "offset=%d | necesita=%d | quedan=%d | data_end=%d",
                local_message,
                global_message,
                name,
                self.reader.offset,
                message_size,
                remaining,
                self.data_end,
            )
            raise RuntimeError(
                f"Mensaje FIT incompleto: {name}"
            )
    
        _LOGGER.debug("")
        _LOGGER.debug(
            "----- DATA %s | local=%d global=%d -----",
            name,
            local_message,
            global_message,
        )
    
        for field in definition["fields"]:
            raw = self.reader.read_bytes(field["size"])
    
            value = self._decode_value(
                raw,
                field["base_type"],
                definition["architecture"],
            )
    
            _LOGGER.debug(
                "FIELD FIT | mensaje=%s | local=%d | campo=%d | "
                "size=%d | type=%s | value=%r | raw=%s",
                name,
                local_message,
                field["number"],
                field["size"],
                self.BASE_TYPES.get(
                    field["base_type"],
                    "UNKNOWN",
                ),
                value,
                raw.hex(" "),
            )

    def _decode_value(
        self,
        raw: bytes,
        base_type: int,
        architecture: int,
    ):
        """Decodifica un valor FIT básico."""

        if base_type == 0x07:
            return raw.split(b"\x00", 1)[0].decode(
                "utf-8",
                errors="replace",
            )

        if base_type in (0x00, 0x02, 0x0A, 0x0D):
            if len(raw) == 1:
                return raw[0]

            return list(raw)

        endian = "<" if architecture == 0 else ">"

        formats = {
            0x01: "b",
            0x83: "h",
            0x84: "H",
            0x85: "i",
            0x86: "I",
            0x88: "f",
            0x89: "d",
            0x8B: "H",
            0x8C: "I",
        }

        fmt = formats.get(base_type)

        if fmt is None:
            return raw.hex()

        expected_size = struct.calcsize(fmt)

        if len(raw) != expected_size:
            return raw.hex()

        return struct.unpack(
            endian + fmt,
            raw,
        )[0]