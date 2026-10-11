"""Tests para los servicios de Coach AI."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.coach_ai.services import async_register_services
from custom_components.coach_ai.models import AthenaResult


@pytest.mark.asyncio
async def test_register_services():

    hass = MagicMock()

    hass.services.async_register = MagicMock()

    hass.data = {"coach_ai": {}}

    await async_register_services(hass)

    hass.services.async_register.assert_called_once()


@pytest.mark.asyncio
async def test_generate_daily_report():

    hass = MagicMock()

    hass.states.async_set = MagicMock()

    hass.services.async_register = MagicMock()

    coordinator = MagicMock()

    coordinator.data = {
        "athena": AthenaResult(
            recovery_score=80,
            fatigue="Baja",
            recommendation="Entrenamiento intenso",
            reasons=["Body Battery alto"],
            training=None,
            nutrition=None,
        )
    }

    hass.data = {
        "coach_ai": {
            "entry": coordinator,
        }
    }

    await async_register_services(hass)

    _, _, callback = hass.services.async_register.call_args[0]

    await callback(AsyncMock())

    hass.states.async_set.assert_called_once()