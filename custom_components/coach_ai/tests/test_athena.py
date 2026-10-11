"""Tests para Athena."""

from custom_components.coach_ai.athena import Athena
from custom_components.coach_ai.models import AthleteState


def athlete(**kwargs):
    """Crea un AthleteState para pruebas."""

    state = AthleteState()

    state.body_battery = kwargs.get("body_battery", 80)
    state.sleep_score = kwargs.get("sleep_score", 85)
    state.training_readiness = kwargs.get("training_readiness", 80)
    state.stress = kwargs.get("stress", 25)
    state.hrv_status = kwargs.get("hrv_status", "Balanced")
    state.resting_hr = kwargs.get("resting_hr", 50)
    state.vo2max = kwargs.get("vo2max", 55)
    state.ftp = kwargs.get("ftp", 250)
    state.ctl = kwargs.get("ctl", 60)
    state.atl = kwargs.get("atl", 55)
    state.tsb = kwargs.get("tsb", 5)

    return state


def history(score: int = 80):
    """Historial simple."""

    return [
        {
            "analysis": {
                "recovery_score": score,
                "recommendation": "Entrenamiento normal",
            }
        }
    ]


def test_hard_training():
    """Debe recomendar entrenamiento intenso."""

    result = Athena().analyse(
        athlete(),
        history(85),
    )

    assert result.recovery_score >= 80
    assert result.recommendation == "Entrenamiento intenso"
    assert result.training is not None


def test_normal_training():
    """Debe recomendar entrenamiento normal."""

    result = Athena().analyse(
        athlete(
            body_battery=65,
            sleep_score=75,
            training_readiness=65,
            stress=45,
        ),
        history(70),
    )

    assert result.recommendation == "Entrenamiento normal"


def test_active_recovery():
    """Debe recomendar recuperación activa."""

    result = Athena().analyse(
        athlete(
            body_battery=35,
            sleep_score=60,
            training_readiness=40,
            stress=70,
            tsb=-15,
        ),
        history(45),
    )

    assert result.recommendation == "Recuperación activa"


def test_rest_day():
    """Debe recomendar descanso."""

    result = Athena().analyse(
        athlete(
            body_battery=10,
            sleep_score=40,
            training_readiness=20,
            stress=95,
            hrv_status="Poor",
            tsb=-30,
        ),
        history(25),
    )

    assert result.recommendation == "Descanso"


def test_training_generated():
    """Siempre debe generar un TrainingPlan."""

    result = Athena().analyse(
        athlete(),
        history(),
    )

    assert result.training is not None
    assert result.training.duration > 0
    assert isinstance(result.training.workout, str)


def test_recovery_limits():
    """Recovery Score entre 0 y 100."""

    result = Athena().analyse(
        athlete(),
        history(),
    )

    assert 0 <= result.recovery_score <= 100


def test_reasons_are_generated():
    """Siempre devuelve una lista de razones."""

    result = Athena().analyse(
        athlete(),
        history(),
    )

    assert isinstance(result.reasons, list)