"""Device triggers for Whoop — use in HA automations."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state as state_trigger
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

TRIGGER_RECOVERY_LOW = "recovery_low"
TRIGGER_RECOVERY_MEDIUM = "recovery_medium"
TRIGGER_RECOVERY_HIGH = "recovery_high"
TRIGGER_NEW_WORKOUT = "new_workout"
TRIGGER_SLEEP_SCORED = "sleep_scored"

TRIGGER_TYPES = {
    TRIGGER_RECOVERY_LOW,
    TRIGGER_RECOVERY_MEDIUM,
    TRIGGER_RECOVERY_HIGH,
    TRIGGER_NEW_WORKOUT,
    TRIGGER_SLEEP_SCORED,
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES)}
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict]:
    return [
        {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: t,
        }
        for t in TRIGGER_TYPES
    ]


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    trigger_type = config[CONF_TYPE]
    entity_id = _entity_for_trigger(hass, config[CONF_DEVICE_ID], trigger_type)

    if entity_id is None:
        return lambda: None

    if trigger_type == TRIGGER_RECOVERY_LOW:
        state_config = {
            "platform": "state",
            "entity_id": entity_id,
        }
        state_config = state_trigger.TRIGGER_SCHEMA(state_config)
        return await state_trigger.async_attach_trigger(
            hass, state_config, action, trigger_info, platform_type="device"
        )

    state_config = {"platform": "state", "entity_id": entity_id}
    state_config = state_trigger.TRIGGER_SCHEMA(state_config)
    return await state_trigger.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )


def _entity_for_trigger(hass: HomeAssistant, device_id: str, trigger_type: str) -> str | None:
    registry = er.async_get(hass)
    key_map = {
        TRIGGER_RECOVERY_LOW: "recovery_score",
        TRIGGER_RECOVERY_MEDIUM: "recovery_score",
        TRIGGER_RECOVERY_HIGH: "recovery_score",
        TRIGGER_NEW_WORKOUT: "workout_strain",
        TRIGGER_SLEEP_SCORED: "sleep_performance",
    }
    key = key_map.get(trigger_type)
    if not key:
        return None
    for entry in er.async_entries_for_device(registry, device_id):
        if entry.unique_id and entry.unique_id.endswith(f"_{key}"):
            return entry.entity_id
    return None
