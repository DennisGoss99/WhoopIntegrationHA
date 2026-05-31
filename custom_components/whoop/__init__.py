"""Whoop integration for Home Assistant."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhoopApi
from .const import COORDINATOR, DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


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

    async def _fetch() -> dict:
        await oauth_session.async_ensure_token_valid()
        api.update_access_token(oauth_session.token["access_token"])

        profile, body, recovery, sleep, cycle, workout = await asyncio.gather(
            api.get_profile(),
            api.get_body_measurement(),
            api.get_latest_recovery(),
            api.get_latest_sleep(),
            api.get_latest_cycle(),
            api.get_latest_workout(),
        )

        if profile is None and cycle is None:
            raise UpdateFailed("Whoop API returned no data")

        return {
            "profile": profile,
            "body": body,
            "recovery": recovery,
            "sleep": sleep,
            "cycle": cycle,
            "workout": workout,
        }

    coordinator = WhoopCoordinator(hass, _fetch)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR: coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class WhoopCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, update_fn) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self._update_fn = update_fn
        self._last_good_data: dict | None = None

    async def _async_update_data(self) -> dict:
        try:
            data = await self._update_fn()
            self._last_good_data = data
            return data
        except UpdateFailed:
            if self._last_good_data is not None:
                _LOGGER.debug("Whoop fetch failed — returning last known data")
                return self._last_good_data
            raise
