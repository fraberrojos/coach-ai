from dataclasses import dataclass

from .models import TrainingPlan
from .models import NutritionPlan


@dataclass(slots=True)
class DailyPlan:

    recovery_score: int

    fatigue: str

    objective: str

    risk: str

    training: TrainingPlan

    nutrition: NutritionPlan | None