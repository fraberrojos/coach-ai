"""Entidad base para Coach AI."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    VERSION,
)


class CoachAIEntity(CoordinatorEntity):
    """Entidad base para todas las entidades de Coach AI."""

    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        """Inicializa la entidad base."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        """Devuelve la información del dispositivo."""
        return DeviceInfo(
            identifiers={(DOMAIN, "coach_ai")},
            name="Coach AI",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
        )

    @property
    def available(self) -> bool:
        """Indica si la entidad está disponible."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict:
        """Atributos comunes para todas las entidades."""

        if self.coordinator.data is None:
            return {}

        athlete = self.coordinator.data.get("athlete")
        athena = self.coordinator.data.get("athena")

        if athlete is None or athena is None:
            return {}

        attrs = {
            "body_battery": athlete.body_battery,
            "sleep_score": athlete.sleep_score,
            "training_readiness": athlete.training_readiness,
            "stress": athlete.stress,
            "hrv_status": athlete.hrv_status,
            "resting_hr": athlete.resting_hr,
            "vo2max": athlete.vo2max,
            "weight": athlete.weight,
            "recovery_score": athena.recovery_score,
            "fatigue": athena.fatigue,
        }

        if athena.training is not None:
            attrs.update(
                {
                    "workout": athena.training.workout,
                    "duration": athena.training.duration,
                    "zone": athena.training.zone,
                    "target_power": athena.training.target_power,
                    "target_hr": athena.training.target_hr,
                    "cadence": athena.training.cadence,
                    "target_tss": athena.training.target_tss,
                    "intensity_factor": athena.training.intensity_factor,
                    "outdoor": athena.training.outdoor,
                    "reason": athena.training.reason,
                }
            )

        return attrs