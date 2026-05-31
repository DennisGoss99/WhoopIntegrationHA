"""Whoop API client — all endpoints use v2."""
from __future__ import annotations

from typing import Any

from aiohttp import ClientSession, ClientResponseError
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"


class WhoopApi:
    def __init__(self, session: ClientSession, access_token: str) -> None:
        self._session = session
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    def update_access_token(self, token: str) -> None:
        self._headers["Authorization"] = f"Bearer {token}"

    async def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{WHOOP_API_BASE}{path}"
        try:
            async with self._session.get(url, headers=self._headers, params=params) as resp:
                if resp.status == 401:
                    raise ConfigEntryAuthFailed("Whoop token expired or invalid")
                if resp.status == 429:
                    raise UpdateFailed("Whoop API rate limit hit")
                resp.raise_for_status()
                return await resp.json()
        except ConfigEntryAuthFailed:
            raise
        except UpdateFailed:
            raise
        except ClientResponseError as err:
            raise UpdateFailed(f"Whoop API error {err.status}: {err.message}") from err

    async def get_profile(self) -> dict | None:
        try:
            return await self._get("/user/profile/basic")
        except UpdateFailed:
            return None

    async def get_body_measurement(self) -> dict | None:
        try:
            return await self._get("/user/measurement/body")
        except UpdateFailed:
            return None

    async def get_latest_recovery(self) -> dict | None:
        try:
            data = await self._get("/recovery", params={"limit": 1})
            records = data.get("records", [])
            return records[0] if records else None
        except UpdateFailed:
            return None

    async def get_latest_sleep(self) -> dict | None:
        try:
            data = await self._get("/activity/sleep", params={"limit": 1})
            records = data.get("records", [])
            return records[0] if records else None
        except UpdateFailed:
            return None

    async def get_latest_cycle(self) -> dict | None:
        try:
            data = await self._get("/cycle", params={"limit": 1})
            records = data.get("records", [])
            return records[0] if records else None
        except UpdateFailed:
            return None

    async def get_latest_workout(self) -> dict | None:
        try:
            data = await self._get("/activity/workout", params={"limit": 1})
            records = data.get("records", [])
            return records[0] if records else None
        except UpdateFailed:
            return None
