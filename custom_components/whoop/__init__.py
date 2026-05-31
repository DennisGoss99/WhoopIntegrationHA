"""Whoop integration for Home Assistant."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from aiohttp import ClientSession
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WhoopApi
from .const import (
    COORDINATOR_DAILY,
    COORDINATOR_HR,
    DAILY_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    HEART_RATE_UPDATE_INTERVAL_SECONDS,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    SCOPES,
)

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

    # Ensure we have a valid token before building the API client
    await oauth_session.async_ensure_token_valid()
    access_token = oauth_session.token["access_token"]

    http_session = async_get_clientsession(hass)
    api = WhoopApi(http_session, access_token)

    async def _refresh_token() -> None:
        """Keep the API client token in sync after OAuth2Session refreshes it."""
        await oauth_session.async_ensure_token_valid()
        api.update_access_token(oauth_session.token["access_token"])

    async def _fetch_daily() -> dict:
        await _refresh_token()
        profile, body, recovery, sleep, cycle, workout = await asyncio.gather(
            api.get_profile(),
            api.get_body_measurement(),
            api.get_latest_recovery(),
            api.get_latest_sleep(),
            api.get_latest_cycle(),
            api.get_latest_workout(),
        )
        # At least one non-None result means the fetch succeeded
        if all(v is None for v in [recovery, sleep, cycle]):
            raise UpdateFailed("All Whoop endpoints returned no data")
        return {
            "profile": profile,
            "body": body,
            "recovery": recovery,
            "sleep": sleep,
            "cycle": cycle,
            "workout": workout,
        }

    async def _fetch_heart_rate() -> int | None:
        await _refresh_token()
        return await api.get_current_heart_rate()

    coordinator_daily = WhoopCoordinator(
        hass,
        name=f"{DOMAIN}_daily_{entry.entry_id}",
        update_fn=_fetch_daily,
        update_interval=timedelta(minutes=DAILY_UPDATE_INTERVAL_MINUTES),
    )
    coordinator_hr = WhoopCoordinator(
        hass,
        name=f"{DOMAIN}_hr_{entry.entry_id}",
        update_fn=_fetch_heart_rate,
        update_interval=timedelta(seconds=HEART_RATE_UPDATE_INTERVAL_SECONDS),
    )

    await coordinator_daily.async_config_entry_first_refresh()
    await coordinator_hr.async_refresh()  # HR may legitimately be None; don't block setup

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR_DAILY: coordinator_daily,
        COORDINATOR_HR: coordinator_hr,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class WhoopCoordinator(DataUpdateCoordinator):
    """Generic coordinator that accepts an async update function."""

    def __init__(self, hass, name, update_fn, update_interval) -> None:
        super().__init__(hass, _LOGGER, name=name, update_interval=update_interval)
        self._update_fn = update_fn
        self._last_good_data = None

    async def _async_update_data(self):
        try:
            result = await self._update_fn()
            # Cache last good data so sensors never go unavailable on transient errors
            if result is not None:
                self._last_good_data = result
            return result if result is not None else self._last_good_data
        except UpdateFailed:
            if self._last_good_data is not None:
                _LOGGER.debug("Whoop fetch failed, returning last known data")
                return self._last_good_data
            raise
