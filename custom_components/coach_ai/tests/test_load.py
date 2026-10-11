"""Tests para LoadEngine."""

from custom_components.coach_ai.load import LoadEngine
from custom_components.coach_ai.models import AthleteState


def make_history(values):
    """Crea un historial con valores TSS."""

    history = []

    for value in values:
        history.append(
            {
                "training": {
                    "target_tss": value,
                }
            }
        )

    return history


def test_empty_history():
    """Historial vacío."""

    athlete = AthleteState()

    athlete = LoadEngine().calculate(
        athlete,
        [],
    )

    assert athlete.ctl == 0.0
    assert athlete.atl == 0.0
    assert athlete.tsb == 0.0


def test_single_training():
    """Un único entrenamiento."""

    athlete = AthleteState()

    history = make_history([100])

    athlete = LoadEngine().calculate(
        athlete,
        history,
    )

    assert athlete.ctl > 0
    assert athlete.atl > 0


def test_constant_training():
    """Entrenamientos constantes."""

    athlete = AthleteState()

    history = make_history([100] * 42)

    athlete = LoadEngine().calculate(
        athlete,
        history,
    )

    assert round(athlete.ctl, 1) == round(100 * 42 / 42, 1)
    assert athlete.atl > 0
    assert athlete.tsb <= athlete.ctl


def test_high_recent_load():
    """ATL debe ser mayor que CTL si hay mucha carga reciente."""

    athlete = AthleteState()

    history = make_history(
        [40] * 35 +
        [200] * 7
    )

    athlete = LoadEngine().calculate(
        athlete,
        history,
    )

    assert athlete.atl > athlete.ctl
    assert athlete.tsb < 0


def test_old_high_load():
    """CTL mayor que ATL si la carga fuerte fue antigua."""

    athlete = AthleteState()

    history = make_history(
        [200] * 35 +
        [20] * 7
    )

    athlete = LoadEngine().calculate(
        athlete,
        history,
    )

    assert athlete.ctl > athlete.atl
    assert athlete.tsb > 0