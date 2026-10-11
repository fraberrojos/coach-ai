"""Cliente MCP Streamable HTTP para el Garmin Bridge de Coach AI."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

DEFAULT_URL = "http://local-garmin-bridge:8000/mcp"
MCP_PROTOCOL_VERSION = "2025-03-26"


class GarminMCPError(RuntimeError):
    """Error al comunicarse con Garmin MCP."""


class GarminMCPClient:
    """Cliente pequeño para el Bridge local, sin depender del SDK MCP."""

    def __init__(
        self,
        url: str = DEFAULT_URL,
        *,
        timeout: int = 60,
    ) -> None:
        self.url = url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session_id: str | None = None
        self._rpc_id = 0
        self._http: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "GarminMCPClient":
        self._http = aiohttp.ClientSession(timeout=self.timeout)
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._http is not None:
            await self._http.close()

    async def initialize(self) -> None:
        """Inicializa una sesión MCP nueva."""
        self._rpc_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "coach-ai",
                    "version": "1.0.0",
                },
            },
        }

        result, session_id = await self._post(payload)
        self._session_id = session_id

        server_info = (
            result.get("result", {}).get("serverInfo", {})
            if isinstance(result, dict)
            else {}
        )

        _LOGGER.info(
            "Coach AI Garmin MCP conectado | servidor=%s | versión=%s",
            server_info.get("name"),
            server_info.get("version"),
        )

        await self._post(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """Ejecuta una herramienta MCP."""
        self._rpc_id += 1

        result, _ = await self._post(
            {
                "jsonrpc": "2.0",
                "id": self._rpc_id,
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments,
                },
            }
        )

        if not isinstance(result, dict):
            raise GarminMCPError(
                f"Respuesta MCP inválida para {name}: {result!r}"
            )

        error = result.get("error")
        if error:
            raise GarminMCPError(
                f"MCP {name}: {error.get('message', error)}"
            )

        return result.get("result")

    async def upload_workout(
        self,
        workout_data: dict[str, Any],
    ) -> Any:
        """Sube un entrenamiento a Garmin Connect sin programarlo."""
        return await self.call_tool(
            "upload_workout",
            {"workout_data": workout_data},
        )

    async def list_tools(self) -> list[dict[str, Any]]:
        """Devuelve las herramientas MCP que expone actualmente el Garmin Bridge."""
        self._rpc_id += 1
        result, _ = await self._post({
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": "tools/list",
            "params": {},
        })

        if not isinstance(result, dict):
            raise GarminMCPError(
                f"Respuesta MCP inválida para tools/list: {result!r}"
            )

        error = result.get("error")
        if error:
            raise GarminMCPError(
                f"MCP tools/list: {error.get('message', error)}"
            )

        payload = result.get("result", {})
        tools = payload.get("tools", []) if isinstance(payload, dict) else []
        return tools if isinstance(tools, list) else []

    @staticmethod
    def extract_workout_id(result: Any) -> int | None:
        """Extrae el ID de workout de una respuesta del Bridge."""
        return _extract_workout_id(result)

    async def upload_workout_with_id(
        self,
        workout_data: dict[str, Any],
    ) -> tuple[Any, int]:
        """Sube un workout y devuelve inmediatamente su ID para poder persistirlo."""
        uploaded = await self.upload_workout(workout_data)
        workout_id = _extract_workout_id(uploaded)
        if workout_id is None:
            raise GarminMCPError(
                f"Garmin no devolvió workout_id: {uploaded!r}"
            )
        return uploaded, workout_id

    async def schedule_workout(
        self,
        workout_id: int | str,
        date: str,
    ) -> Any:
        """Programa un entrenamiento en Garmin Connect."""
        return await self.call_tool(
            "schedule_workout",
            {
                "workout_id": int(workout_id),
                "calendar_date": date,
            },
        )

    async def get_scheduled_workouts(
        self,
        start_date: str,
        end_date: str,
    ) -> Any:
        """Consulta eventos del calendario Garmin entre dos fechas inclusivas."""
        return await self.call_tool(
            "get_scheduled_workouts",
            {"start_date": start_date, "end_date": end_date},
        )

    async def unschedule_workout(self, scheduled_workout_id: int | str) -> Any:
        """Quita un evento del calendario sin borrar la plantilla del workout."""
        return await self.call_tool(
            "unschedule_workout",
            {"scheduled_workout_id": int(scheduled_workout_id)},
        )

    async def upload_and_schedule(
        self,
        workout_data: dict[str, Any],
        date: str,
    ) -> tuple[Any, Any]:
        """Sube y después programa un entrenamiento."""
        uploaded = await self.upload_workout(workout_data)

        workout_id = _extract_workout_id(uploaded)
        if workout_id is None:
            raise GarminMCPError(
                f"Garmin no devolvió workout_id: {uploaded!r}"
            )

        scheduled = await self.schedule_workout(workout_id, date)
        return uploaded, scheduled

    async def _post(
        self,
        payload: dict[str, Any],
    ) -> tuple[Any, str | None]:
        if self._http is None:
            raise GarminMCPError("El cliente Garmin MCP no está iniciado.")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        try:
            async with self._http.post(
                self.url,
                json=payload,
                headers=headers,
            ) as response:
                body = await response.text()

                if response.status >= 400:
                    raise GarminMCPError(
                        f"HTTP {response.status} en Garmin MCP: "
                        f"{body[:1000]}"
                    )

                session_id = response.headers.get("Mcp-Session-Id")
                return (
                    _parse_mcp_response(body),
                    session_id or self._session_id,
                )

        except aiohttp.ClientError as err:
            raise GarminMCPError(
                f"No se puede conectar con Garmin Bridge "
                f"({self.url}): {err}"
            ) from err


def _parse_mcp_response(body: str) -> Any:
    """Acepta respuestas JSON normales o SSE."""
    body = body.strip()

    if not body:
        return {}

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        pass

    for line in body.splitlines():
        if line.startswith("data:"):
            data = line[5:].strip()

            if not data or data == "[DONE]":
                continue

            try:
                return json.loads(data)
            except json.JSONDecodeError:
                continue

    raise GarminMCPError(
        f"Respuesta MCP no reconocida: {body[:1000]}"
    )


def extract_records(result: Any) -> list[dict[str, Any]]:
    """Extrae registros de respuestas MCP directas o envueltas en content/text JSON."""
    found: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            # Una entrada de calendario suele tener scheduled_workout_id y workout_id.
            if any(key in value for key in ("scheduled_workout_id", "scheduledWorkoutId")):
                found.append(value)
                return
            for key in ("scheduled_workouts", "workouts", "items", "results", "data"):
                child = value.get(key)
                if isinstance(child, (list, dict)):
                    visit(child)
            content = value.get("content")
            if isinstance(content, list):
                visit(content)
            for item in content if isinstance(content, list) else []:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        visit(json.loads(item.get("text", "")))
                    except (TypeError, ValueError, json.JSONDecodeError):
                        pass
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            try:
                visit(json.loads(value))
            except (TypeError, ValueError, json.JSONDecodeError):
                pass

    visit(result)
    # Evita repetir el mismo registro si la respuesta incluye varias envolturas.
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in found:
        key = (str(record.get("scheduled_workout_id", record.get("scheduledWorkoutId", ""))),
               str(record.get("workout_id", record.get("workoutId", ""))))
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique


def _extract_workout_id(result: Any) -> int | None:
    """Extrae workout_id de las respuestas habituales del servidor."""
    if isinstance(result, dict):
        for key in ("workout_id", "workoutId", "id"):
            value = result.get(key)

            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    pass

        content = result.get("content")

        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue

                if item.get("type") != "text":
                    continue

                try:
                    nested = json.loads(item.get("text", ""))
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue

                found = _extract_workout_id(nested)

                if found is not None:
                    return found

    return None


def build_garmin_cycling_workout(
    *,
    name: str,
    description: str,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """Convierte pasos de Coach AI a la estructura Garmin.

    Cada paso debe contener:
      name, duration, target_type, target_low, target_high

    Para potencia absoluta se usa el formato validado por Garmin:
      ID 2 / power.zone + targetValueOne/targetValueTwo,
      sin zoneNumber.
    """

    workout_steps: list[dict[str, Any]] = []

    for order, step in enumerate(steps, start=1):
        duration = max(0, int(step.get("duration") or 0))

        item: dict[str, Any] = {
            "type": "ExecutableStepDTO",
            "stepOrder": order,
            "stepType": {
                "stepTypeId": 3,
                "stepTypeKey": "interval",
            },
            "endCondition": {
                "conditionTypeId": 2,
                "conditionTypeKey": "time",
            },
            "endConditionValue": float(duration),
        }

        target_type = step.get("target_type")
        low = step.get("target_low")
        high = step.get("target_high")

        if target_type == "power" and low is not None and high is not None:
            item["targetType"] = {
                "workoutTargetTypeId": 2,
                "workoutTargetTypeKey": "power.zone",
            }
            item["targetValueOne"] = float(low)
            item["targetValueTwo"] = float(high)

        elif (
            target_type == "heart_rate"
            and low is not None
            and high is not None
        ):
            item["targetType"] = {
                "workoutTargetTypeId": 4,
                "workoutTargetTypeKey": "heart.rate.zone",
            }
            item["targetValueOne"] = float(low)
            item["targetValueTwo"] = float(high)

        elif target_type == "cadence" and low is not None and high is not None:
            # Se añadirá el mapping canónico de cadencia después de
            # validarlo contra el Bridge actual.
            item["targetValueOne"] = float(low)
            item["targetValueTwo"] = float(high)

        workout_steps.append(item)

    return {
        "workoutName": name[:100],
        "description": description[:1000],
        "sportType": {
            "sportTypeId": 2,
            "sportTypeKey": "cycling",
        },
        "workoutSegments": [
            {
                "segmentOrder": 1,
                "sportType": {
                    "sportTypeId": 2,
                    "sportTypeKey": "cycling",
                },
                "workoutSteps": workout_steps,
            }
        ],
    }
