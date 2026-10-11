"""Recovery Engine de Coach AI."""

from __future__ import annotations


class RecoveryEngine:
    """Calcula el Recovery Score del deportista."""

    def calculate(
        self,
        *,
        body_battery: int | None,
        sleep_score: int | None,
        stress: int | None,
        hrv_status: str | None,
        training_readiness: int | None = None,
        ctl: float | None = None,
        atl: float | None = None,
        tsb: float | None = None,
    ) -> tuple[int, list[str]]:
        """Calcula la puntuación de recuperación."""

        score = 50
        reasons: list[str] = []

        # -------------------------
        # Body Battery
        # -------------------------

        if body_battery is not None:

            if body_battery >= 90:
                score += 25
                reasons.append("Body Battery completamente recuperado.")

            elif body_battery >= 75:
                score += 18
                reasons.append("Body Battery alto.")

            elif body_battery >= 50:
                score += 10

            elif body_battery >= 30:
                score -= 5
                reasons.append("Body Battery bajo.")

            else:
                score -= 20
                reasons.append("Body Battery muy bajo.")

        # -------------------------
        # Sueño
        # -------------------------

        if sleep_score is not None:

            if sleep_score >= 90:
                score += 15
                reasons.append("Sueño excelente.")

            elif sleep_score >= 80:
                score += 10

            elif sleep_score >= 70:
                score += 5

            elif sleep_score >= 60:
                score -= 5

            else:
                score -= 15
                reasons.append("Sueño insuficiente.")

        # -------------------------
        # Estrés
        # -------------------------

        if stress is not None:

            if stress <= 20:
                score += 10

            elif stress <= 40:
                score += 5

            elif stress <= 60:
                pass

            elif stress <= 80:
                score -= 10
                reasons.append("Estrés elevado.")

            else:
                score -= 20
                reasons.append("Estrés muy elevado.")

        # -------------------------
        # HRV
        # -------------------------

        if hrv_status:

            value = hrv_status.lower()

            if "balanced" in value:
                score += 10
                reasons.append("HRV equilibrada.")

            elif "low" in value:
                score -= 10
                reasons.append("HRV baja.")

            elif "poor" in value:
                score -= 15
                reasons.append("HRV muy baja.")

        # -------------------------
        # Training Readiness
        # -------------------------

        if training_readiness is not None:

            if training_readiness >= 80:
                score += 10

            elif training_readiness >= 60:
                score += 5

            elif training_readiness >= 40:
                pass

            else:
                score -= 10
                reasons.append("Training Readiness baja.")

        # -------------------------
        # ATL / CTL / TSB
        # -------------------------

        if tsb is not None:

            if tsb < -20:
                score -= 15
                reasons.append("Fatiga acumulada elevada.")

            elif tsb < -10:
                score -= 8

            elif tsb > 10:
                score += 5
                reasons.append("Buena frescura para entrenar.")

        score = max(0, min(100, round(score)))

        return score, reasons