"""Whoop calendar — shows workouts and sleep sessions in HA calendar."""
from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COORDINATOR_CYCLE, DOMAIN
from . import WhoopCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WhoopCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR_CYCLE]
    profile = (coordinator.data or {}).get("profile") or {}
    user_id = profile.get("user_id", "unknown")

    from homeassistant.helpers import config_entry_oauth2_flow
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from .api import WhoopApi

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    await oauth_session.async_ensure_token_valid()
    api = WhoopApi(async_get_clientsession(hass), oauth_session.token["access_token"])

    async_add_entities([
        WhoopWorkoutCalendar(api, user_id, profile),
        WhoopSleepCalendar(api, user_id, profile),
    ])


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _device_info(user_id: str, profile: dict) -> dict:
    first = profile.get("first_name", "")
    last = profile.get("last_name", "")
    return {
        "identifiers": {(DOMAIN, str(user_id))},
        "name": f"Whoop ({first} {last})".strip(),
        "manufacturer": "Whoop",
        "model": "Whoop Band",
    }


class WhoopWorkoutCalendar(CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Workouts"
    _attr_icon = "mdi:weight-lifter"

    def __init__(self, api, user_id: str, profile: dict) -> None:
        self._api = api
        self._attr_unique_id = f"whoop_{user_id}_calendar_workouts"
        self._attr_device_info = _device_info(user_id, profile)
        self._events: list[CalendarEvent] = []

    @property
    def event(self) -> CalendarEvent | None:
        return self._events[0] if self._events else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        records = await self._api.get_workouts(limit=25)
        events = []
        for r in records:
            start = _parse_dt(r.get("start"))
            end = _parse_dt(r.get("end"))
            if not start or not end:
                continue
            if end < start_date or start > end_date:
                continue
            score = r.get("score") or {}
            sport = r.get("sport_name") or "Workout"
            strain = score.get("strain")
            avg_hr = score.get("average_heart_rate")
            summary = sport
            description = []
            if strain is not None:
                description.append(f"Strain: {strain:.1f}")
            if avg_hr is not None:
                description.append(f"Avg HR: {avg_hr} bpm")
            events.append(CalendarEvent(
                start=start,
                end=end,
                summary=summary,
                description=", ".join(description) or None,
            ))
        self._events = events
        return events

    async def async_update(self) -> None:
        self._events = await self._api.get_workouts(limit=25)


class WhoopSleepCalendar(CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "Sleep"
    _attr_icon = "mdi:sleep"

    def __init__(self, api, user_id: str, profile: dict) -> None:
        self._api = api
        self._attr_unique_id = f"whoop_{user_id}_calendar_sleep"
        self._attr_device_info = _device_info(user_id, profile)
        self._events: list[CalendarEvent] = []

    @property
    def event(self) -> CalendarEvent | None:
        return self._events[0] if self._events else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        records = await self._api.get_sleeps(limit=25)
        events = []
        for r in records:
            start = _parse_dt(r.get("start"))
            end = _parse_dt(r.get("end"))
            if not start or not end:
                continue
            if end < start_date or start > end_date:
                continue
            score = r.get("score") or {}
            is_nap = r.get("nap", False)
            performance = score.get("sleep_performance_percentage")
            summary = "Nap" if is_nap else "Sleep"
            description = []
            if performance is not None:
                description.append(f"Performance: {performance}%")
            events.append(CalendarEvent(
                start=start,
                end=end,
                summary=summary,
                description=", ".join(description) or None,
            ))
        self._events = events
        return events

    async def async_update(self) -> None:
        self._events = await self._api.get_sleeps(limit=25)
