"""Diagnostics support for Coach AI."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for Coach AI."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    athlete = coordinator.data.get("athlete")
    athena = coordinator.data.get("athena")

    return {
        "integration": "Coach AI",
        "version": "1.0.0",
        "history_records": coordinator.data.get("history_records"),
        "last_analysis": coordinator.data.get("last_analysis"),
        "ctl": coordinator.data.get("ctl"),
        "atl": coordinator.data.get("atl"),
        "tsb": coordinator.data.get("tsb"),
        "athlete": repr(athlete) if athlete else None,
        "athena": repr(athena) if athena else None,
    }