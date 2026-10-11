"""Tests para TrendEngine."""

from custom_components.coach_ai.trend import TrendEngine


def make_record(score: int, recommendation: str = "Entrenamiento normal"):
    """Crea un registro de historial."""

    return {
        "analysis": {
            "recovery_score": score,
            "recommendation": recommendation,
        }
    }


def test_empty_history():
    """Historial vacío."""

    result = TrendEngine().analyse([])

    assert result.average_recovery == 0
    assert result.recovery_trend == "unknown"
    assert result.fatigue_days == 0
    assert result.consecutive_training_days == 0
    assert result.risk_overtraining is False


def test_improving_trend():
    """La recuperación mejora."""

    history = [
        make_record(45),
        make_record(55),
        make_record(65),
        make_record(75),
        make_record(85),
    ]

    result = TrendEngine().analyse(history)

    assert result.recovery_trend == "improving"
    assert result.average_recovery > 60


def test_declining_trend():
    """La recuperación empeora."""

    history = [
        make_record(90),
        make_record(80),
        make_record(70),
        make_record(60),
        make_record(40),
    ]

    result = TrendEngine().analyse(history)

    assert result.recovery_trend == "declining"


def test_stable_trend():
    """La recuperación permanece estable."""

    history = [make_record(70) for _ in range(7)]

    result = TrendEngine().analyse(history)

    assert result.recovery_trend == "stable"
    assert result.average_recovery == 70


def test_overtraining_detection():
    """Detecta riesgo de sobreentrenamiento."""

    history = [
        make_record(40),
        make_record(35),
        make_record(45),
        make_record(42),
        make_record(38),
        make_record(36),
        make_record(39),
    ]

    result = TrendEngine().analyse(history)

    assert result.fatigue_days >= 3
    assert result.risk_overtraining is True


def test_low_training_load():
    """Carga baja."""

    history = [
        make_record(80),
        make_record(85, "Descanso"),
        make_record(82, "Descanso"),
    ]

    result = TrendEngine().analyse(history)

    assert result.training_load == "low"


def test_medium_training_load():
    """Carga media."""

    history = [
        make_record(80),
        make_record(80),
        make_record(80),
        make_record(80, "Descanso"),
    ]

    result = TrendEngine().analyse(history)

    assert result.training_load == "medium"


def test_high_training_load():
    """Carga alta."""

    history = [
        make_record(70),
        make_record(70),
        make_record(70),
        make_record(70),
        make_record(70),
        make_record(80, "Descanso"),
    ]

    result = TrendEngine().analyse(history)

    assert result.training_load == "high"


def test_very_high_training_load():
    """Carga muy alta."""

    history = [make_record(75) for _ in range(7)]

    result = TrendEngine().analyse(history)

    assert result.training_load == "very_high"