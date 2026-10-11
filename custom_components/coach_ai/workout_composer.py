"""Compositor inteligente de entrenamientos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkoutBlock:
    """Bloque de entrenamiento."""

    name: str
    duration: int
    repeats: int = 1
    recovery: int = 0
    cadence: int = 90
    power_factor: float | None = None
    heart_rate: int | None = None
    step_type: str = "interval"
    intensity: str = "active"


class WorkoutComposer:
    """Compone la estructura del entrenamiento."""

    def compose(
        self,
        workout: str,
        duration: int,
        recovery: int,
        volume_factor: float = 1.0,
    ) -> list[WorkoutBlock]:
        """Compone la estructura del entrenamiento."""

        workout = workout.lower()

        # ---------------------------------
        # SWEET SPOT
        # ---------------------------------

        if workout == "sweet spot":

            warmup = 15
            cooldown = 10

            if duration >= 110:
                if recovery >= 90:
                    repeats = 6
                elif recovery >= 75:
                    repeats = 5
                elif recovery >= 60:
                    repeats = 4
                else:
                    repeats = 3

            elif duration >= 75:
                if recovery >= 90:
                    repeats = 5
                elif recovery >= 75:
                    repeats = 4
                elif recovery >= 60:
                    repeats = 3
                else:
                    repeats = 2

            else:
                if recovery >= 90:
                    repeats = 4
                elif recovery >= 75:
                    repeats = 3
                elif recovery >= 60:
                    repeats = 2
                else:
                    repeats = 1

            repeats = max(
                1,
                round(repeats * volume_factor),
            )

            return [
                WorkoutBlock(
                    name="Warmup",
                    step_type="warmup",
                    intensity="warmup",
                    duration=warmup,
                    cadence=85,
                    power_factor=0.50,
                ),
                WorkoutBlock(
                    name="Sweet Spot",
                    step_type="interval",
                    intensity="active",
                    duration=8,
                    repeats=repeats,
                    recovery=4,
                    cadence=92,
                    power_factor=0.88,
                ),
                WorkoutBlock(
                    name="Cooldown",
                    step_type="cooldown",
                    intensity="cooldown",
                    duration=cooldown,
                    cadence=85,
                    power_factor=0.45,
                ),
            ]

        # ---------------------------------
        # VO2 MAX
        # ---------------------------------

        if workout == "vo2 max":

            if recovery >= 90:
                repeats = 6
            elif recovery >= 75:
                repeats = 5
            elif recovery >= 60:
                repeats = 4
            else:
                repeats = 3

            repeats = max(
                1,
                round(repeats * volume_factor),
            )

            return [
                WorkoutBlock(
                    name="Warmup",
                    step_type="warmup",
                    intensity="warmup",
                    duration=15,
                    cadence=85,
                    power_factor=0.50,
                ),
                WorkoutBlock(
                    name="VO2",
                    step_type="interval",
                    intensity="active",
                    duration=4,
                    repeats=repeats,
                    recovery=4,
                    cadence=100,
                    power_factor=1.05,
                ),
                WorkoutBlock(
                    name="Cooldown",
                    step_type="cooldown",
                    intensity="cooldown",
                    duration=10,
                    cadence=85,
                    power_factor=0.45,
                ),
            ]

        # ---------------------------------
        # THRESHOLD
        # ---------------------------------

        if workout == "threshold":

            if recovery >= 90:
                repeats = 5
            elif recovery >= 75:
                repeats = 4
            elif recovery >= 60:
                repeats = 3
            else:
                repeats = 2

            repeats = max(
                1,
                round(repeats * volume_factor),
            )

            return [
                WorkoutBlock(
                    name="Warmup",
                    step_type="warmup",
                    intensity="warmup",
                    duration=15,
                    cadence=85,
                    power_factor=0.50,
                ),
                WorkoutBlock(
                    name="Threshold",
                    step_type="interval",
                    intensity="active",
                    duration=10,
                    repeats=repeats,
                    recovery=5,
                    cadence=92,
                    power_factor=1.00,
                ),
                WorkoutBlock(
                    name="Cooldown",
                    step_type="cooldown",
                    intensity="cooldown",
                    duration=10,
                    cadence=85,
                    power_factor=0.45,
                ),
            ]

        # ---------------------------------
        # ENDURANCE / Z2
        # ---------------------------------

        if workout in (
            "endurance",
            "resistencia z2",
            "fondo",
        ):

            base = max(
                duration - 25,
                20,
            )

            base = int(
                base * volume_factor
            )

            if recovery >= 85:
                base += 15
            elif recovery >= 70:
                base += 5
            elif recovery <= 40:
                base -= 15

            base = max(
                20,
                base,
            )

            return [
                WorkoutBlock(
                    name="Warmup",
                    step_type="warmup",
                    intensity="warmup",
                    duration=15,
                    cadence=85,
                    power_factor=0.50,
                ),
                WorkoutBlock(
                    name="Z2",
                    step_type="interval",
                    intensity="active",
                    duration=base,
                    cadence=90,
                    power_factor=0.65,
                ),
                WorkoutBlock(
                    name="Cooldown",
                    step_type="cooldown",
                    intensity="cooldown",
                    duration=10,
                    cadence=85,
                    power_factor=0.45,
                ),
            ]

        # ---------------------------------
        # TEMPO
        # ---------------------------------

        if workout == "tempo":

            if recovery >= 85:
                repeats = 3
            elif recovery >= 65:
                repeats = 2
            else:
                repeats = 1

            repeats = max(
                1,
                round(repeats * volume_factor),
            )

            return [
                WorkoutBlock(
                    name="Warmup",
                    step_type="warmup",
                    intensity="warmup",
                    duration=15,
                    cadence=85,
                    power_factor=0.50,
                ),
                WorkoutBlock(
                    name="Tempo",
                    step_type="interval",
                    intensity="active",
                    duration=15,
                    repeats=repeats,
                    recovery=5,
                    cadence=90,
                    power_factor=0.80,
                ),
                WorkoutBlock(
                    name="Cooldown",
                    step_type="cooldown",
                    intensity="cooldown",
                    duration=10,
                    cadence=85,
                    power_factor=0.45,
                ),
            ]

        # ---------------------------------
        # LONG RIDE / Z2
        # ---------------------------------

        if workout in (
            "long ride",
            "long",
            "long_ride",
        ):
            return [
                WorkoutBlock(
                    name="Zona 2",
                    step_type="interval",
                    intensity="active",
                    duration=duration,
                    cadence=85,
                    power_factor=0.65,
                )
            ]

        # ---------------------------------
        # RECOVERY / RODAJE
        # ---------------------------------

        return [
            WorkoutBlock(
                name="Rodaje",
                step_type="interval",
                intensity="active",
                duration=duration,
                cadence=90,
                power_factor=0.45,
            )
        ]