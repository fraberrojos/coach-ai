"""Score de carga."""

from __future__ import annotations


class LoadScoreEngine:
    """Calcula un score de carga."""

    def calculate(
        self,
        ctl: float | None,
        atl: float | None,
        tsb: float | None,
    ) -> int:

        ctl = ctl or 0
        atl = atl or 0
        tsb = tsb or 0

        score = 50

        score += min(int(ctl), 30)

        if -10 <= tsb <= 10:
            score += 20
        elif -20 <= tsb <= 20:
            score += 10

        if atl > ctl + 20:
            score -= 20

        return max(0, min(score, 100))