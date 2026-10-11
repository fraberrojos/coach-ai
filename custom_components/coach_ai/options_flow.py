from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import OptionsFlowWithReload

from .const import (
    DEFAULT_DEFAULT_FTP,
    DEFAULT_MAX_DURATION,
    DEFAULT_NOTIFICATIONS,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_UPDATE_INTERVAL,
)


class CoachAIOptionsFlow(OptionsFlowWithReload):
    """Opciones de Coach AI."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Gestiona las opciones de la integración."""

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "update_interval",
                        default=self.config_entry.options.get(
                            "update_interval",
                            DEFAULT_UPDATE_INTERVAL,
                        ),
                    ): vol.All(int, vol.Range(min=1, max=1440)),

                    vol.Required(
                        "notify_service",
                        default=self.config_entry.options.get(
                            "notify_service",
                            DEFAULT_NOTIFY_SERVICE,
                        ),
                    ): str,

                    vol.Required(
                        "default_ftp",
                        default=self.config_entry.options.get(
                            "default_ftp",
                            DEFAULT_DEFAULT_FTP,
                        ),
                    ): vol.All(int, vol.Range(min=100, max=600)),

                    vol.Required(
                        "max_duration",
                        default=self.config_entry.options.get(
                            "max_duration",
                            DEFAULT_MAX_DURATION,
                        ),
                    ): vol.All(int, vol.Range(min=15, max=600)),

                    vol.Required(
                        "notifications",
                        default=self.config_entry.options.get(
                            "notifications",
                            DEFAULT_NOTIFICATIONS,
                        ),
                    ): bool,
                }
            ),
        )