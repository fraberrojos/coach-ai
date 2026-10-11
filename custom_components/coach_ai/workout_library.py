"""Biblioteca de entrenamientos."""

from __future__ import annotations

from .workout_definition import WorkoutDefinition


# =============================================================
# DEFINICIONES BASE
# =============================================================

WORKOUTS = {
    # ---------------------------------------------------------
    # DESCANSO
    # ---------------------------------------------------------

    "rest": {
        "workout": "Rest",
        "duration": 0,
        "zone": "REST",
        "power_factor": None,
        "cadence": None,
        "target_tss": 0,
        "intensity_factor": 0.0,
        "outdoor": False,
        "reason": "Descanso",
        "intervals": [],
    },

    # ---------------------------------------------------------
    # RECOVERY
    # ---------------------------------------------------------

    "recovery": {
        "workout": "Recovery",
        "duration": 40,
        "zone": "Z1",
        "power_factor": 0.45,
        "cadence": 90,
        "target_tss": 20,
        "intensity_factor": 0.45,
        "outdoor": False,
        "reason": "Recuperación activa",
        "intervals": [
            {
                "name": "Recovery",
                "duration": 40,
                "power_factor": 0.45,
                "cadence": 90,
            }
        ],
    },

    # ---------------------------------------------------------
    # ENDURANCE
    # ---------------------------------------------------------

    "endurance": {
        "workout": "Endurance",
        "duration": 90,
        "zone": "Z2",
        "power_factor": 0.65,
        "cadence": 90,
        "target_tss": 60,
        "intensity_factor": 0.65,
        "outdoor": True,
        "reason": "Base aeróbica",
        "intervals": [
            {
                "name": "Zona 2",
                "duration": 90,
                "power_factor": 0.65,
                "cadence": 90,
            }
        ],
    },

    # ---------------------------------------------------------
    # SWEET SPOT
    # ---------------------------------------------------------

    "sweet spot": {
        "workout": "Sweet Spot",
        "duration": 75,
        "zone": "Z4",
        "power_factor": 0.88,
        "cadence": 92,
        "target_tss": 85,
        "intensity_factor": 0.88,
        "outdoor": True,
        "reason": "Desarrollo FTP",
        "intervals": [
            {
                "name": "Calentamiento",
                "duration": 15,
                "power_factor": 0.55,
                "cadence": 85,
            },
            {
                "name": "Sweet Spot",
                "duration": 45,
                "power_factor": 0.88,
                "cadence": 92,
            },
            {
                "name": "Enfriamiento",
                "duration": 15,
                "power_factor": 0.50,
                "cadence": 85,
            },
        ],
    },

    # ---------------------------------------------------------
    # TEMPO
    # ---------------------------------------------------------

    "tempo": {
        "workout": "Tempo",
        "duration": 60,
        "zone": "Z3",
        "power_factor": 0.80,
        "cadence": 90,
        "target_tss": 70,
        "intensity_factor": 0.80,
        "outdoor": True,
        "reason": "Mejora del ritmo sostenible",
        "intervals": [
            {
                "name": "Calentamiento",
                "duration": 10,
                "power_factor": 0.55,
                "cadence": 85,
            },
            {
                "name": "Tempo",
                "duration": 40,
                "power_factor": 0.80,
                "cadence": 90,
            },
            {
                "name": "Enfriamiento",
                "duration": 10,
                "power_factor": 0.50,
                "cadence": 85,
            },
        ],
    },

    # ---------------------------------------------------------
    # THRESHOLD
    # ---------------------------------------------------------

    "threshold": {
        "workout": "Threshold",
        "duration": 70,
        "zone": "Z4",
        "power_factor": 1.00,
        "cadence": 92,
        "target_tss": 90,
        "intensity_factor": 0.95,
        "outdoor": True,
        "reason": "Trabajo de umbral",
        "intervals": [
            {
                "name": "Calentamiento",
                "duration": 15,
                "power_factor": 0.55,
                "cadence": 85,
            },
            {
                "name": "Threshold",
                "duration": 40,
                "power_factor": 1.00,
                "cadence": 92,
            },
            {
                "name": "Enfriamiento",
                "duration": 15,
                "power_factor": 0.50,
                "cadence": 85,
            },
        ],
    },

    # ---------------------------------------------------------
    # VO2 MAX
    # ---------------------------------------------------------

    "vo2 max": {
        "workout": "VO2 Max",
        "duration": 60,
        "zone": "Z5",
        "power_factor": 1.05,
        "cadence": 100,
        "target_tss": 95,
        "intensity_factor": 0.95,
        "outdoor": True,
        "reason": "Mejora del VO₂ máximo",
        "intervals": [
            {
                "name": "Calentamiento",
                "duration": 15,
                "power_factor": 0.55,
                "cadence": 85,
            },
            {
                "name": "VO2 Max",
                "duration": 30,
                "power_factor": 1.05,
                "cadence": 100,
            },
            {
                "name": "Enfriamiento",
                "duration": 15,
                "power_factor": 0.50,
                "cadence": 85,
            },
        ],
    },
}


# =============================================================
# BIBLIOTECA INTELIGENTE
# =============================================================


class WorkoutLibrary:
    """Biblioteca inteligente de entrenamientos."""

    def __init__(self) -> None:
        """Inicializa la biblioteca."""

        self.workouts = [
            WorkoutDefinition(
                name="Recovery",
                workout_key="recovery",
                goal="recovery",
                min_duration=30,
                max_duration=60,
                min_recovery=0,
                target_tss=20,
                intensity_factor=0.45,
                priority=100,
                zone="Z1",
                cadence=90,
                outdoor=False,
                reason="Recuperación activa",
                power_factor=0.45,
            ),

            WorkoutDefinition(
                name="Endurance",
                workout_key="endurance",
                goal="maintenance",
                min_duration=45,
                max_duration=180,
                min_recovery=40,
                target_tss=60,
                intensity_factor=0.65,
                priority=80,
                zone="Z2",
                cadence=90,
                outdoor=True,
                reason="Base aeróbica",
                power_factor=0.65,
            ),

            WorkoutDefinition(
                name="Sweet Spot",
                workout_key="sweet spot",
                goal="ftp",
                min_duration=60,
                max_duration=120,
                min_recovery=70,
                target_tss=85,
                intensity_factor=0.88,
                priority=100,
                zone="Z4",
                cadence=92,
                outdoor=True,
                reason="Desarrollo del FTP",
                power_factor=0.88,
            ),

            WorkoutDefinition(
                name="VO2 Max",
                workout_key="vo2 max",
                goal="vo2",
                min_duration=50,
                max_duration=90,
                min_recovery=80,
                target_tss=95,
                intensity_factor=0.95,
                priority=90,
                zone="Z5",
                cadence=100,
                outdoor=True,
                reason="Mejora del VO₂ máximo",
                power_factor=1.05,
            ),

            WorkoutDefinition(
                name="Tempo",
                workout_key="tempo",
                goal="maintenance",
                min_duration=50,
                max_duration=90,
                min_recovery=50,
                target_tss=70,
                intensity_factor=0.80,
                priority=85,
                zone="Z3",
                cadence=90,
                outdoor=True,
                reason="Mejora del ritmo sostenido",
                power_factor=0.80,
            ),

            WorkoutDefinition(
                name="Threshold",
                workout_key="threshold",
                goal="ftp",
                min_duration=60,
                max_duration=90,
                min_recovery=80,
                target_tss=90,
                intensity_factor=0.95,
                priority=95,
                zone="Z4",
                cadence=92,
                outdoor=True,
                reason="Trabajo específico de umbral",
                power_factor=1.00,
            ),
        ]

    def search(
        self,
        goal: str,
        duration: int,
        recovery: int,
    ) -> WorkoutDefinition:
        """Busca el entrenamiento más adecuado."""

        candidates: list[WorkoutDefinition] = []

        for workout in self.workouts:

            if workout.goal != goal:
                continue

            if duration < workout.min_duration:
                continue

            if recovery < workout.min_recovery:
                continue

            candidates.append(workout)

        if not candidates:
            return self.workouts[0]

        return max(
            candidates,
            key=lambda workout: workout.priority,
        )