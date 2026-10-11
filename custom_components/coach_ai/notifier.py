"""Sistema de notificaciones de Coach AI."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

from .const import DEFAULT_NOTIFY_SERVICE

_LOGGER = logging.getLogger(__name__)


class CoachAINotifier:
    """Sistema de notificaciones de Coach AI."""

    def __init__(
        self,
        hass: HomeAssistant,
        notify_service: str = DEFAULT_NOTIFY_SERVICE,
    ) -> None:
        """Inicializa el notificador."""

        self.hass = hass
        self.notify_service = notify_service

    async def send(
        self,
        title: str,
        message: str,
        data: dict | None = None,
    ) -> bool:
        """Envía una notificación y devuelve True si se ha enviado."""

        if "." not in self.notify_service:
            _LOGGER.error(
                "Coach AI NOTIFY: servicio inválido: %s",
                self.notify_service,
            )
            return False

        domain, service = self.notify_service.split(".", 1)

        if not self.hass.services.has_service(domain, service):
            services = self.hass.services.async_services()
            available = sorted(
                services.get("notify", {}).keys()
            )
            _LOGGER.error(
                "Coach AI NOTIFY: servicio no disponible: %s.%s | "
                "servicios notify disponibles=%s",
                domain,
                service,
                available,
            )
            return False

        try:
            await self.hass.services.async_call(
                domain,
                service,
                {
                    "title": title,
                    "message": message,
                    "data": data or {},
                },
                blocking=True,
            )
            _LOGGER.debug(
                "Coach AI NOTIFY: enviado correctamente mediante %s",
                self.notify_service,
            )
            return True

        except Exception:
            _LOGGER.exception(
                "Coach AI NOTIFY: error enviando mediante %s",
                self.notify_service,
            )
            return False
