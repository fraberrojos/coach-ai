"""Tests para Config Flow."""

from unittest.mock import MagicMock

import pytest

from custom_components.coach_ai.config_flow import CoachAIConfigFlow
from homeassistant.data_entry_flow import FlowResultType


@pytest.mark.asyncio
async def test_user_flow():
    """Comprueba que el flujo de configuración se inicia correctamente."""

    flow = CoachAIConfigFlow()

    flow.hass = MagicMock()

    result = await flow.async_step_user()

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_create_entry():
    """Comprueba que se crea la entrada."""

    flow = CoachAIConfigFlow()

    flow.hass = MagicMock()

    result = await flow.async_step_user(
        user_input={}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Coach AI"