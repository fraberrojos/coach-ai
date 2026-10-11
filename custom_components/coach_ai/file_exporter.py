"""Exporta archivos al sistema."""

from __future__ import annotations

from pathlib import Path


class FileExporter:
    """Guarda archivos generados por Coach AI."""

    def __init__(self) -> None:
        self.output = Path("/config/www/coach_ai")
        self.output.mkdir(parents=True, exist_ok=True)

    def save_fit(
        self,
        filename: str,
        data: bytes,
    ) -> str:
        """Guarda un archivo FIT."""

        path = self.output / filename

        path.write_bytes(data)

        return str(path)