"""Diagnostics for Whoop integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import COORDINATOR_CYCLE, COORDINATOR_DAILY, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    data = hass.data[DOMAIN][entry.entry_id]

    cycle_data = data[COORDINATOR_CYCLE].data or {}
    daily_data = data[COORDINATOR_DAILY].data or {}

    # Redact personal info
    profile = dict(cycle_data.get("profile") or {})
    profile.pop("email", None)
    profile.pop("first_name", None)
    profile.pop("last_name", None)

    return {
        "entry_id": entry.entry_id,
        "profile": profile,
        "cycle": cycle_data.get("cycle"),
        "recovery": daily_data.get("recovery"),
        "sleep": daily_data.get("sleep"),
        "workout": daily_data.get("workout"),
        "body": daily_data.get("body"),
    }
