"""Muestra las definiciones de un archivo FIT."""

from __future__ import annotations

from pathlib import Path

from .fit_parser import FitParser


def dump(filename: str) -> None:
    print()
    print("#" * 80)
    print(filename)
    print("#" * 80)

    data = Path(filename).read_bytes()

    FitParser(data).parse()