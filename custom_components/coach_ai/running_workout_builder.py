"""Generador de sesiones estructuradas de running, independiente del ciclismo."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RunningStep:
    """Paso exportable de una sesión de carrera."""
    name: str
    duration_min: int
    step_type: str
    intensity: str = "active"
    target_hr_low: int | None = None
    target_hr_high: int | None = None
    target_pace_fast_sec_km: int | None = None
    target_pace_slow_sec_km: int | None = None

    def __post_init__(self) -> None:
        if self.duration_min <= 0:
            raise ValueError("La duración de cada paso debe ser positiva.")
        if self.step_type not in {"warmup", "interval", "recovery", "cooldown"}:
            raise ValueError(f"Tipo de paso no válido: {self.step_type}")


@dataclass(slots=True)
class RunningWorkout:
    """Sesión de carrera con bloques ordenados."""
    name: str
    workout_type: str
    duration_min: int
    steps: list[RunningStep] = field(default_factory=list)
    rationale: str = ""

    def validate(self) -> None:
        if not self.steps:
            raise ValueError("La sesión debe contener pasos.")
        if self.steps[0].step_type != "warmup":
            raise ValueError("La sesión debe empezar con calentamiento.")
        if self.steps[-1].step_type != "cooldown":
            raise ValueError("La sesión debe terminar con vuelta a la calma.")
        actual = sum(step.duration_min for step in self.steps)
        if actual != self.duration_min:
            raise ValueError(f"Duración declarada ({self.duration_min}) distinta de la suma de pasos ({actual}).")


class RunningWorkoutBuilder:
    """Compone rodajes e intervalos con calentamiento y vuelta a la calma explícitos."""
    def easy_run(self, duration_min: int = 35) -> RunningWorkout:
        if duration_min < 20:
            raise ValueError("Un rodaje fácil debe durar al menos 20 minutos.")
        warmup = min(8, max(5, duration_min // 5))
        cooldown = min(5, max(3, duration_min // 8))
        main = duration_min - warmup - cooldown
        workout = RunningWorkout(
            name="Running fácil", workout_type="easy", duration_min=duration_min,
            rationale="Rodaje conversacional para construir base aeróbica.",
            steps=[
                RunningStep("Calentamiento suave", warmup, "warmup", "easy"),
                RunningStep("Rodaje fácil", main, "interval", "easy"),
                RunningStep("Vuelta a la calma", cooldown, "cooldown", "easy"),
            ],
        )
        workout.validate()
        return workout

    def intervals(self, *, duration_min: int = 40, repetitions: int = 5,
                  effort_min: int = 3, recovery_min: int = 2) -> RunningWorkout:
        if repetitions < 1 or effort_min < 1 or recovery_min < 1:
            raise ValueError("Repeticiones y duraciones deben ser positivas.")
        warmup, cooldown = 10, 5
        main_minutes = duration_min - warmup - cooldown
        required = repetitions * effort_min + (repetitions - 1) * recovery_min
        if main_minutes < required:
            raise ValueError("La duración no permite incluir intervalos, recuperaciones, calentamiento y vuelta a la calma.")
        steps = [RunningStep("Calentamiento progresivo", warmup, "warmup", "easy")]
        for index in range(repetitions):
            steps.append(RunningStep(f"Intervalo {index + 1}", effort_min, "interval", "hard"))
            if index < repetitions - 1:
                steps.append(RunningStep(f"Recuperación {index + 1}", recovery_min, "recovery", "easy"))
        remaining = main_minutes - required
        if remaining:
            steps.append(RunningStep("Carrera suave adicional", remaining, "interval", "easy"))
        steps.append(RunningStep("Vuelta a la calma", cooldown, "cooldown", "easy"))
        workout = RunningWorkout(
            name=f"Running intervalos {repetitions}x{effort_min} min",
            workout_type="intervals", duration_min=duration_min, steps=steps,
            rationale="Intervalos separados por recuperaciones explícitas.",
        )
        workout.validate()
        return workout
