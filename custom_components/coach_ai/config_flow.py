from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from .const import DOMAIN
from .options_flow import CoachAIOptionsFlow


class CoachAIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow de Coach AI."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ):
        """Devuelve el flujo de opciones."""
        return CoachAIOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Crear la integración."""

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Coach AI",
                data={},
            )

        return self.async_show_form(
            step_id="user",
        )