"""Servicios de Coach AI."""

from __future__ import annotations
from functools import partial

import logging
from datetime import date

from homeassistant.core import HomeAssistant, ServiceCall

from .athena import Athena
from .garmin_fit import GarminFitBuilder
from .garmin_mcp_client import GarminMCPClient, build_garmin_cycling_workout
from .garmin_compare import compare_garmin_schedule
from .exporter import WorkoutExporter
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_register_services(hass: HomeAssistant) -> None:
    """Registra los servicios de Coach AI."""


    async def generate_daily_report(call: ServiceCall) -> None:
        """Genera el informe diario."""
        coordinators = hass.data.get(DOMAIN, {})

        if not coordinators:
            _LOGGER.warning("No hay instancias de Coach AI cargadas.")
            return

        for coordinator in coordinators.values():
            if coordinator.data is None:
                continue

            athena = coordinator.data.get("athena")
            if athena is None:
                continue

            report = Athena().daily_report(athena)
            hass.states.async_set("sensor.coach_ai_daily_report", report)

        _LOGGER.debug("Informe diario generado.")

    async def export_workout(call: ServiceCall) -> None:
        """Exporta el entrenamiento actual."""
        coordinators = hass.data.get(DOMAIN, {})

        if not coordinators:
            _LOGGER.warning("No hay instancias de Coach AI cargadas.")
            return

        for coordinator in coordinators.values():
            if coordinator.data is None:
                continue

            athena = coordinator.data.get("athena")
            if athena is None:
                continue

            if athena.training is None:
                continue

            builder = GarminFitBuilder()
            workout = builder.build(athena.training)

            exporter = WorkoutExporter(hass)
            path = await exporter.export_json(workout)

            _LOGGER.info("Entrenamiento exportado: %s", path)

    async def upload_workout_to_garmin(call: ServiceCall) -> None:
        """Sube el entrenamiento actual a Garmin Connect sin programarlo."""
        coordinators = hass.data.get(DOMAIN, {})

        if not coordinators:
            _LOGGER.warning("No hay instancias de Coach AI cargadas.")
            return

        for coordinator in coordinators.values():
            if coordinator.data is None:
                continue

            athena = coordinator.data.get("athena")
            if athena is None or athena.training is None:
                continue

            builder = GarminFitBuilder()
            workout = builder.build(athena.training)

            steps = [
                {
                    "name": step.name,
                    "duration": step.duration,
                    "target_type": step.target_type,
                    "target_low": step.target_low,
                    "target_high": step.target_high,
                }
                for step in workout.steps
            ]

            workout_data = build_garmin_cycling_workout(
                name=workout.name,
                description=workout.description,
                steps=steps,
            )

            _LOGGER.info(
                "Coach AI Garmin: subiendo entrenamiento | nombre=%s | pasos=%s",
                workout.name,
                len(steps),
            )

            async with GarminMCPClient() as client:
                result = await client.upload_workout(workout_data)

            _LOGGER.info(
                "Coach AI Garmin: entrenamiento subido correctamente | resultado=%s",
                result,
            )

    async def upload_and_schedule_workout_to_garmin(call: ServiceCall) -> None:
        """Sube el entrenamiento actual y lo programa en Garmin Connect."""
        _LOGGER.info(
            "Coach AI Garmin DEBUG: datos recibidos por el servicio | data=%s",
            dict(call.data),
        )

        requested_date = call.data.get("date")

        if not requested_date:
            _LOGGER.error(
                "Coach AI Garmin: falta el campo 'date' | data=%s",
                dict(call.data),
            )
            return

        try:
            scheduled_date = date.fromisoformat(str(requested_date))
        except ValueError:
            _LOGGER.error(
                "Coach AI Garmin: fecha no válida '%s'. "
                "Usa formato YYYY-MM-DD.",
                requested_date,
            )
            return

        date_text = scheduled_date.isoformat()
        coordinators = hass.data.get(DOMAIN, {})

        if not coordinators:
            _LOGGER.warning("No hay instancias de Coach AI cargadas.")
            return

        for coordinator in coordinators.values():
            if coordinator.data is None:
                continue

            athena = coordinator.data.get("athena")
            if athena is None or athena.training is None:
                continue

            builder = GarminFitBuilder()
            workout = builder.build(athena.training)

            steps = [
                {
                    "name": step.name,
                    "duration": step.duration,
                    "target_type": step.target_type,
                    "target_low": step.target_low,
                    "target_high": step.target_high,
                }
                for step in workout.steps
            ]

            workout_data = build_garmin_cycling_workout(
                name=workout.name,
                description=workout.description,
                steps=steps,
            )

            _LOGGER.info(
                "Coach AI Garmin: subiendo y programando | "
                "nombre=%s | fecha=%s | pasos=%s",
                workout.name,
                date_text,
                len(steps),
            )

            async with GarminMCPClient() as client:
                result = await client.upload_and_schedule(
                    workout_data=workout_data,
                    date=date_text,
                )

            _LOGGER.info(
                "Coach AI Garmin: entrenamiento programado correctamente | "
                "fecha=%s | resultado=%s",
                date_text,
                result,
            )

    async def garmin_check_schedule(call: ServiceCall) -> None:
        """Consulta Garmin sin crear, subir ni programar entrenamientos."""
        _LOGGER.warning(
            "Coach AI Garmin DIAGNOSTICO: consultando entrenamientos programados."
        )

        try:
            async with GarminMCPClient() as client:
                result = await client.call_tool(
                    "get_scheduled_workouts",
                    {
                    "start_date": "2026-09-26",
                    "end_date": "2026-10-03",
                    },
                )

            _LOGGER.warning(
                "Coach AI Garmin DIAGNOSTICO: get_scheduled_workouts | resultado=%s",
                result,
            )

        except Exception:
            _LOGGER.exception(
                "Coach AI Garmin DIAGNOSTICO: error consultando "
                "get_scheduled_workouts"
            )

    hass.services.async_register(
        DOMAIN,
        "generate_daily_report",
        generate_daily_report,
    )
    hass.services.async_register(
        DOMAIN,
        "export_workout",
        export_workout,
    )
    hass.services.async_register(
        DOMAIN,
        "upload_workout_to_garmin",
        upload_workout_to_garmin,
    )
    hass.services.async_register(
        DOMAIN,
        "upload_and_schedule_workout_to_garmin",
        upload_and_schedule_workout_to_garmin,
    )
    hass.services.async_register(
        DOMAIN,
        "garmin_check_schedule",
        garmin_check_schedule,
    hass.services.async_register(
        DOMAIN,
        "garmin_compare_schedule",
        lambda call: hass.async_create_task(compare_garmin_schedule(hass)),
    )
    )
