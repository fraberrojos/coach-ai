"""Zonas de entrenamiento."""

from __future__ import annotations


class Zones:
    """Calcula las zonas de potencia."""

    def __init__(self, ftp: int):
        self.ftp = ftp or 250

    @property
    def z1(self):
        return int(self.ftp * 0.55)

    @property
    def z2(self):
        return int(self.ftp * 0.70)

    @property
    def z3(self):
        return int(self.ftp * 0.85)

    @property
    def z4(self):
        return int(self.ftp * 1.00)

    @property
    def z5(self):
        return int(self.ftp * 1.15)

    @property
    def sweetspot(self):
        return int(self.ftp * 0.92)