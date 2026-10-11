"""Tests para RecoveryEngine."""

from custom_components.coach_ai.recovery import RecoveryEngine


def test_full_recovery():
    """Atleta completamente recuperado."""

    engine = RecoveryEngine()

    score, reasons = engine.calculate(
        body_battery=100,
        sleep_score=95,
        stress=10,
        hrv_status="Balanced",
        training_readiness=95,
        ctl=60,
        atl=50,
        tsb=10,
    )

    assert score >= 90
    assert len(reasons) > 0


def test_medium_recovery():
    """Recuperación media."""

    engine = RecoveryEngine()

    score, reasons = engine.calculate(
        body_battery=60,
        sleep_score=75,
        stress=45,
        hrv_status="Balanced",
        training_readiness=60,
        ctl=50,
        atl=55,
        tsb=-5,
    )

    assert 55 <= score <= 85
    assert isinstance(reasons, list)


def test_poor_recovery():
    """Recuperación muy baja."""

    engine = RecoveryEngine()

    score, reasons = engine.calculate(
        body_battery=15,
        sleep_score=45,
        stress=90,
        hrv_status="Poor",
        training_readiness=20,
        ctl=80,
        atl=110,
        tsb=-30,
    )

    assert score < 40
    assert len(reasons) >= 3


def test_limits():
    """El Recovery Score siempre debe estar entre 0 y 100."""

    engine = RecoveryEngine()

    score, _ = engine.calculate(
        body_battery=100,
        sleep_score=100,
        stress=0,
        hrv_status="Balanced",
        training_readiness=100,
        ctl=0,
        atl=0,
        tsb=50,
    )

    assert score <= 100

    score, _ = engine.calculate(
        body_battery=0,
        sleep_score=0,
        stress=100,
        hrv_status="Poor",
        training_readiness=0,
        ctl=100,
        atl=200,
        tsb=-100,
    )

    assert score >= 0