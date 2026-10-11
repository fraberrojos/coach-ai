"""Constructor inteligente de intervalos."""

from __future__ import annotations

from .models import Interval
from .workout_composer import WorkoutComposer


class IntervalBuilder:
    """Genera intervalos automáticamente."""

    def __init__(self) -> None:
        """Inicializa el compositor."""

        self.composer = WorkoutComposer()

    @staticmethod
    def _calculate_power(
        ftp: float | None,
        power_factor: float | None,
    ) -> int | None:
        """Calcula la potencia del intervalo."""

        if ftp is None:
            return None

        if power_factor is None:
            return None

        return round(ftp * power_factor)

    @staticmethod
    def _fit_intervals_to_duration(
        intervals: list[Interval],
        target_duration: int,
    ) -> list[Interval]:
        """Ajusta los intervalos para que sumen exactamente la duración."""

        if not intervals:
            return intervals

        target_duration = max(1, int(target_duration))

        current_duration = sum(
            max(1, int(interval.duration))
            for interval in intervals
        )

        if current_duration == target_duration:
            return intervals

        # ---------------------------------------------------------
        # AUMENTAR DURACIÓN
        # ---------------------------------------------------------

        if target_duration > current_duration:

            extra = target_duration - current_duration

            active_indexes = [
                index
                for index, interval in enumerate(intervals)
                if (
                    getattr(interval, "step_type", "interval")
                    not in {
                        "warmup",
                        "cooldown",
                        "recovery",
                    }
                )
                and not interval.name.lower().startswith("recuper")
            ]

            if not active_indexes:
                active_indexes = [len(intervals) - 1]

            # Repartimos el tiempo adicional entre los bloques
            # principales de trabajo.
            base = extra // len(active_indexes)
            remainder = extra % len(active_indexes)

            for position, index in enumerate(active_indexes):

                intervals[index].duration += base

                if position < remainder:
                    intervals[index].duration += 1

            return intervals

        # ---------------------------------------------------------
        # REDUCIR DURACIÓN
        # ---------------------------------------------------------

        reduction = current_duration - target_duration

        # Primero reducimos los bloques de trabajo.
        adjustable = [
            index
            for index, interval in enumerate(intervals)
            if (
                getattr(interval, "step_type", "interval")
                not in {
                    "warmup",
                    "cooldown",
                }
            )
        ]

        if not adjustable:
            adjustable = list(range(len(intervals)))

        for index in reversed(adjustable):

            if reduction <= 0:
                break

            interval = intervals[index]

            removable = max(
                0,
                int(interval.duration) - 1,
            )

            delta = min(
                removable,
                reduction,
            )

            interval.duration -= delta
            reduction -= delta

        # Si todavía necesitamos reducir tiempo,
        # permitimos reducir cualquier bloque manteniendo
        # al menos 1 minuto.
        if reduction > 0:

            for index in reversed(range(len(intervals))):

                if reduction <= 0:
                    break

                interval = intervals[index]

                removable = max(
                    0,
                    int(interval.duration) - 1,
                )

                delta = min(
                    removable,
                    reduction,
                )

                interval.duration -= delta
                reduction -= delta

        return intervals

    def build(
        self,
        workout: str,
        duration: int,
        recovery: int,
        volume_factor: float = 1.0,
        ftp: float | None = None,
    ) -> list[Interval]:
        """Construye los intervalos del entrenamiento."""

        blocks = self.composer.compose(
            workout,
            duration,
            recovery,
            volume_factor,
        )

        intervals: list[Interval] = []

        for block in blocks:

            power = self._calculate_power(
                ftp,
                block.power_factor,
            )

            # -----------------------------------------------------
            # BLOQUE SIN REPETICIONES
            # -----------------------------------------------------

            if block.repeats == 1:

                intervals.append(
                    Interval(
                        name=block.name,
                        duration=block.duration,
                        power=power,
                        heart_rate=block.heart_rate,
                        cadence=block.cadence,
                        step_type=block.step_type,
                        intensity=block.intensity,
                    )
                )

                continue

            # -----------------------------------------------------
            # BLOQUES REPETIDOS
            # -----------------------------------------------------

            for i in range(block.repeats):

                intervals.append(
                    Interval(
                        name=f"{block.name} {i + 1}",
                        duration=block.duration,
                        power=power,
                        heart_rate=block.heart_rate,
                        cadence=block.cadence,
                        step_type=block.step_type,
                        intensity=block.intensity,
                    )
                )

                # Recuperación entre repeticiones.
                if block.recovery > 0:

                    recovery_power = self._calculate_power(
                        ftp,
                        0.45,
                    )

                    intervals.append(
                        Interval(
                            name="Recuperación",
                            duration=block.recovery,
                            power=recovery_power,
                            heart_rate=None,
                            cadence=85,
                            step_type="recovery",
                            intensity="rest",
                        )
                    )

        # ---------------------------------------------------------
        # AJUSTAR DURACIÓN TOTAL
        # ---------------------------------------------------------

        intervals = self._fit_intervals_to_duration(
            intervals,
            duration,
        )

        return intervals