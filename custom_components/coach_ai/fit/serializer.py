"""Serializador FIT."""

from __future__ import annotations

from .binary import FitBinaryWriter
from .message import FitMessage
from .messages import MessageDefinition


class FitSerializer:
    """Serializa mensajes FIT."""

    def __init__(self) -> None:
        self.writer = FitBinaryWriter()

    def write_record_header(
        self,
        local_message: int,
        definition: bool = False,
    ) -> None:
        """Escribe un Record Header."""

        header = local_message & 0x0F

        if definition:
            header |= 0x40

        self.writer.write_uint8(header)

    def _write_field(
        self,
        size: int,
        base_type: int,
        value,
    ) -> None:
        """Escribe un campo FIT respetando su tipo."""

        if isinstance(value, str):
            encoded = value.encode("utf-8")[: size - 1]
            encoded += b"\x00"
            encoded = encoded.ljust(size, b"\x00")

            self.writer.write_bytes(encoded)
            return

        if isinstance(value, bytes):
            if len(value) != size:
                raise ValueError(
                    f"FIT bytes incorrectos: "
                    f"esperados={size}, recibidos={len(value)}"
                )

            self.writer.write_bytes(value)
            return

        value = int(value)

        # ENUM / UINT8 / UINT8Z / BYTE
        if base_type in (
            0x00,
            0x02,
            0x0A,
            0x0D,
        ):
            if size != 1:
                raise ValueError(
                    f"Tipo FIT de 1 byte con tamaño {size}"
                )

            self.writer.write_uint8(value)
            return

        # SINT8
        if base_type == 0x01:
            if size != 1:
                raise ValueError(
                    "SINT8 debe ocupar 1 byte"
                )

            self.writer.write_sint8(value)
            return

        # UINT16 / UINT16Z
        if base_type in (
            0x84,
            0x8B,
        ):
            if size != 2:
                raise ValueError(
                    "UINT16 debe ocupar 2 bytes"
                )

            self.writer.write_uint16(value)
            return

        # SINT16
        if base_type == 0x83:
            if size != 2:
                raise ValueError(
                    "SINT16 debe ocupar 2 bytes"
                )

            self.writer.write_sint16(value)
            return

        # UINT32 / UINT32Z
        if base_type in (
            0x86,
            0x8C,
        ):
            if size != 4:
                raise ValueError(
                    "UINT32 debe ocupar 4 bytes"
                )

            self.writer.write_uint32(value)
            return

        # SINT32
        if base_type == 0x85:
            if size != 4:
                raise ValueError(
                    "SINT32 debe ocupar 4 bytes"
                )

            self.writer.write_sint32(value)
            return

        raise ValueError(
            f"Tipo FIT no soportado: "
            f"0x{base_type:02X}, size={size}"
        )

    def serialize(
        self,
        definition: MessageDefinition,
        message: FitMessage,
    ) -> None:
        """Serializa un Data Message."""

        self.write_record_header(
            message.local_message,
        )

        values = message.field_map()

        for definition_field in definition.fields:

            field = values.get(
                definition_field.number
            )

            if field is None:
                available = sorted(values.keys())

                raise ValueError(
                    f"\n"
                    f"Mensaje: {type(message).__name__}\n"
                    f"Global : {message.global_message}\n"
                    f"Falta  : {definition_field.number}\n"
                    f"Tiene  : {available}"
                )

            self._write_field(
                definition_field.size,
                definition_field.base_type,
                field.value,
            )

    def serialize_definition(
        self,
        definition: MessageDefinition,
    ) -> None:
        """Serializa un Definition Message."""

        self.write_record_header(
            definition.local_message,
            definition=True,
        )

        # Reserved
        self.writer.write_uint8(0)

        # Architecture = 0 → little endian
        self.writer.write_uint8(0)

        self.writer.write_uint16(
            definition.global_message
        )

        self.writer.write_uint8(
            len(definition.fields)
        )

        for field in definition.fields:

            self.writer.write_uint8(
                field.number
            )

            self.writer.write_uint8(
                field.size
            )

            self.writer.write_uint8(
                field.base_type
            )