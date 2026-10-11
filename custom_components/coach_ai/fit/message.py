"""Mensajes FIT."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FitField:
    """Valor de un campo FIT."""

    number: int
    value: int | str | bytes
    
@dataclass(slots=True)
class FitMessage:
    """Mensaje FIT."""

    local_message: int
    global_message: int

    fields: list[FitField]
    
    def field_map(self) -> dict[int, FitField]:
        """Devuelve los campos indexados por número."""
    
        return {
            field.number: field
            for field in self.fields
        }