from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from .garmin_mcp_client import GarminMCPClient

_LOGGER = logging.getLogger(__name__)


def _normalise_name(value):
    """Normaliza un nombre de entrenamiento."""
    return " ".join(str(value or "").lower().split())


def _is_rest(workout) -> bool:
    """Devuelve True si el entrenamiento es descanso."""
    if not isinstance(workout, dict):
        return False

    value = workout.get("workout") or workout.get("name", "")

    return _normalise_name(value) in ("rest", "descanso")


def _unwrap_schedule(result):
    """Extrae la respuesta real devuelta por el cliente MCP."""
    if isinstance(result, dict):
        content = result.get("content")

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")

                    try:
                        return json.loads(text)
                    except (json.JSONDecodeError, TypeError):
                        pass

            return content

    return result


__all__ = ["compare_garmin_schedule"]


async def compare_garmin_schedule(hass):
    """Compara los entrenamientos programados en Garmin para la semana actual."""

    today = date.today()

    # Lunes de la semana actual
    monday = today - timedelta(days=today.weekday())

    start_date = monday.isoformat()
    end_date = (monday + timedelta(days=6)).isoformat()

    _LOGGER.warning(
        "Coach AI Garmin COMPARADOR: consultando %s -> %s",
        start_date,
        end_date,
    )

    try:
        async with GarminMCPClient() as client:
            result = await client.call_tool(
                "get_scheduled_workouts",
                {
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )

        # Extraer la respuesta real del MCP
        scheduled = _unwrap_schedule(result)

        if isinstance(scheduled, dict):
            workouts = scheduled.get("scheduled_workouts", [])

            if not isinstance(workouts, list):
                _LOGGER.warning(
                    "Coach AI Garmin COMPARADOR: "
                    "scheduled_workouts no es una lista: %s",
                    workouts,
                )
                return

            if not workouts:
                _LOGGER.warning(
                    "Coach AI Garmin COMPARADOR: "
                    "no hay entrenamientos programados entre %s y %s",
                    start_date,
                    end_date,
                )
                return

            for workout in workouts:
                if not isinstance(workout, dict):
                    continue

                _LOGGER.warning(
                    "Coach AI Garmin COMPARADOR: "
                    "Garmin programado: fecha=%s sid=%s "
                    "workout_id=%s nombre=%s completado=%s",
                    workout.get("date"),
                    workout.get("scheduled_workout_id"),
                    workout.get("workout_id"),
                    workout.get("name")
                    or workout.get("workout"),
                    workout.get("completed"),
                )

        else:
            _LOGGER.warning(
                "Coach AI Garmin COMPARADOR: respuesta GARMIN = %s",
                scheduled,
            )

    except Exception:
        _LOGGER.exception(
            "Coach AI Garmin COMPARADOR: error consultando Garmin"
        )
