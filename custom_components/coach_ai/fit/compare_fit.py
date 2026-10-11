"""Compara un FIT Garmin con uno generado por Coach AI."""

from __future__ import annotations

from pathlib import Path

from .fit_compare import FitCompare


def main() -> None:

    garmin = Path("garmin.fit").read_bytes()
    coach = Path("coach.fit").read_bytes()

    FitCompare().compare(
        garmin,
        coach,
    )


if __name__ == "__main__":
    main()