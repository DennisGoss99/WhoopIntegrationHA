"""Whoop integration for Home Assistant."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow, entity_registry as er, device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhoopApi
from .const import (
    COORDINATOR_CYCLE,
    COORDINATOR_DAILY,
    CYCLE_UPDATE_INTERVAL_MINUTES,
    DAILY_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    await oauth_session.async_ensure_token_valid()

    api = WhoopApi(async_get_clientsession(hass), oauth_session.token["access_token"])

    async def _refresh_token() -> None:
        await oauth_session.async_ensure_token_valid()
        api.update_access_token(oauth_session.token["access_token"])

    async def _fetch_cycle() -> dict:
        await _refresh_token()
        profile, cycle = await asyncio.gather(
            api.get_profile(),
            api.get_latest_cycle(),
        )
        if cycle is None:
            raise UpdateFailed("Whoop cycle endpoint returned no data")
        return {"profile": profile, "cycle": cycle}

    async def _fetch_daily() -> dict:
        await _refresh_token()
        profile, recovery, sleep, workout, body = await asyncio.gather(
            api.get_profile(),
            api.get_latest_recovery(),
            api.get_latest_sleep(),
            api.get_latest_workout(),
            api.get_body_measurement(),
        )
        return {
            "profile": profile,
            "recovery": recovery,
            "sleep": sleep,
            "workout": workout,
            "body": body,
        }

    coordinator_cycle = WhoopCoordinator(
        hass,
        name=f"{DOMAIN}_cycle",
        update_fn=_fetch_cycle,
        update_interval=timedelta(minutes=CYCLE_UPDATE_INTERVAL_MINUTES),
    )
    coordinator_daily = WhoopCoordinator(
        hass,
        name=f"{DOMAIN}_daily",
        update_fn=_fetch_daily,
        update_interval=timedelta(minutes=DAILY_UPDATE_INTERVAL_MINUTES),
    )

    await coordinator_cycle.async_config_entry_first_refresh()
    await coordinator_daily.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR_CYCLE: coordinator_cycle,
        COORDINATOR_DAILY: coordinator_daily,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Clean up stale "unknown" entities/devices from older versions
    _async_cleanup_unknown_device(hass, entry)

    return True


def _async_cleanup_unknown_device(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove leftover entities and device created when user_id was not yet known."""
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    stale_entities = [
        e for e in er.async_entries_for_config_entry(entity_reg, entry.entry_id)
        if e.unique_id and "whoop_unknown_" in e.unique_id
    ]
    for entity_entry in stale_entities:
        _LOGGER.debug("Removing stale entity: %s", entity_entry.entity_id)
        entity_reg.async_remove(entity_entry.entity_id)

    stale_devices = dr.async_entries_for_config_entry(device_reg, entry.entry_id)
    for device in stale_devices:
        identifiers = {i[1] for i in device.identifiers if i[0] == DOMAIN}
        if "unknown" in identifiers:
            _LOGGER.debug("Removing stale device: %s", device.id)
            device_reg.async_remove_device(device.id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class WhoopCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, name, update_fn, update_interval) -> None:
        super().__init__(hass, _LOGGER, name=name, update_interval=update_interval)
        self._update_fn = update_fn
        self._last_good_data = None

    async def _async_update_data(self) -> dict:
        try:
            data = await self._update_fn()
            self._last_good_data = data
            return data
        except UpdateFailed:
            if self._last_good_data is not None:
                _LOGGER.debug("%s fetch failed — returning last known data", self.name)
                return self._last_good_data
            raise
