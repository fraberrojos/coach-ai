"""Explicaciones de Coach AI."""

from __future__ import annotations

from .models import AthleteState


class ExplainEngine:
    """Genera explicaciones en lenguaje natural."""

    def build(
        self,
        athlete: AthleteState,
        recovery_score: int,
        workout: str,
    ) -> str:
        """Explica la recomendación."""

        reasons = []

        if athlete.body_battery is not None:
            reasons.append(
                f"Body Battery {athlete.body_battery}%."
            )

        if athlete.sleep_score is not None:
            reasons.append(
                f"Sueño {athlete.sleep_score}%."
            )

        if athlete.training_readiness is not None:
            reasons.append(
                f"Training Readiness {athlete.training_readiness}."
            )

        if athlete.tsb is not None:
            reasons.append(
                f"TSB {athlete.tsb:.1f}."
            )

        reasons.append(
            f"Recovery Score {recovery_score}%."
        )

        return (
            f"Se recomienda '{workout}' porque "
            + " ".join(reasons)
        )