"""Tests para CoachAICoordinator."""

import pytest
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.coach_ai.coordinator import CoachAICoordinator
from custom_components.coach_ai.models import AthleteState, AthenaResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def hass():
    return MagicMock()


@pytest.fixture
def coordinator(hass):
    return CoachAICoordinator(hass)


@pytest.fixture
def default_athlete():
    return AthleteState()


@pytest.fixture
def default_result():
    return AthenaResult(
        recovery_score=80,
        fatigue="Baja",
        recommendation="Entrenamiento intenso",
        reasons=[],
        training=None,
        nutrition=None,
    )


def patch_coordinator(coordinator, athlete, result, history=None):
    """Aplica todos los patches necesarios para _async_update_data."""
    return (
        patch.object(coordinator.builder, "build", return_value=athlete),
        patch.object(coordinator.history, "load", return_value=history or []),
        patch.object(coordinator.load_engine, "calculate", return_value=athlete),
        patch.object(coordinator.athena, "analyse", return_value=result),
        patch.object(coordinator.history, "save", new_callable=AsyncMock),
    )


# ── Tests: camino feliz ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_returns_athlete_and_athena_result(
    coordinator, default_athlete, default_result
):
    """El dict devuelto contiene las claves esperadas con los objetos correctos."""
    patches = patch_coordinator(coordinator, default_athlete, default_result)

    with ExitStack() as stack:
        for patcher in patches:
            stack.enter_context(patcher)
        data = await coordinator._async_update_data()

    assert data["athlete"] is default_athlete
    assert data["athena"] is default_result


@pytest.mark.asyncio
async def test_history_save_called_once(coordinator, default_athlete, default_result):
    """El coordinador persiste el resultado tras cada actualización."""
    patches = patch_coordinator(coordinator, default_athlete, default_result)

    with ExitStack() as stack:
        mocks = [stack.enter_context(patcher) for patcher in patches]
        await coordinator._async_update_data()

    save_mock = mocks[-1]  # último patch → history.save
    save_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_load_engine_receives_athlete_from_builder(
    coordinator, default_athlete, default_result
):
    """load_engine.calculate recibe el atleta que construyó builder.build."""
    patches = patch_coordinator(coordinator, default_athlete, default_result)

    with ExitStack() as stack:
        mocks = [stack.enter_context(patcher) for patcher in patches]
        await coordinator._async_update_data()

    calculate_mock = mocks[2]
    calculate_mock.assert_called_once_with(default_athlete, [])


# ── Tests: manejo de errores ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_raises_when_athena_fails(coordinator, default_athlete):
    """Si Athena falla, el coordinador propaga la excepción (HA la captura)."""
    with (
        patch.object(coordinator.builder, "build", return_value=default_athlete),
        patch.object(coordinator.history, "load", return_value=[]),
        patch.object(coordinator.load_engine, "calculate", return_value=default_athlete),
        patch.object(
            coordinator.athena, "analyse", side_effect=RuntimeError("API timeout")
        ),
        patch.object(coordinator.history, "save", new_callable=AsyncMock),
    ):
        with pytest.raises(RuntimeError, match="API timeout"):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_update_raises_when_builder_fails(coordinator):
    """Si builder.build falla, el flujo se interrumpe antes de llamar a Athena."""
    athena_mock = MagicMock()

    with (
        patch.object(
            coordinator.builder, "build", side_effect=ValueError("sensor missing")
        ),
        patch.object(coordinator.athena, "analyse", athena_mock),
    ):
        with pytest.raises(ValueError, match="sensor missing"):
            await coordinator._async_update_data()

    athena_mock.assert_not_called()