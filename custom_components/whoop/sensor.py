"""Whoop sensors — cycle (10min) + daily (60min) coordinators."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WhoopCoordinator
from .const import COORDINATOR_CYCLE, COORDINATOR_DAILY, DOMAIN


def _safe(data: dict | None, *keys: str) -> Any:
    node = data
    for k in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(k)
    return node


@dataclass(frozen=True)
class WhoopSensorDesc(SensorEntityDescription):
    value_fn: Callable[[dict], Any] = field(default=lambda _: None)
    attr_fn: Callable[[dict], dict] = field(default=lambda _: {})


# ── Cycle sensors (update every 10 min) ──────────────────────────────────────

CYCLE_SENSORS: tuple[WhoopSensorDesc, ...] = (
    WhoopSensorDesc(
        key="cycle_state",
        name="Cycle State",
        icon="mdi:fire",
        value_fn=lambda d: _safe(d, "cycle", "score_state"),
    ),
    WhoopSensorDesc(
        key="day_strain",
        name="Day Strain",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire",
        value_fn=lambda d: _safe(d, "cycle", "score", "strain"),
        attr_fn=lambda d: _safe(d, "cycle", "score") or {},
    ),
    WhoopSensorDesc(
        key="day_kilojoules",
        name="Day Kilojoules",
        native_unit_of_measurement="kJ",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire-circle",
        value_fn=lambda d: _safe(d, "cycle", "score", "kilojoule"),
    ),
    WhoopSensorDesc(
        key="day_avg_heart_rate",
        name="Day Average Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-outline",
        value_fn=lambda d: _safe(d, "cycle", "score", "average_heart_rate"),
    ),
    WhoopSensorDesc(
        key="day_max_heart_rate",
        name="Day Max Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-circle",
        value_fn=lambda d: _safe(d, "cycle", "score", "max_heart_rate"),
    ),
)

# ── Daily sensors (update every 60 min) ──────────────────────────────────────

DAILY_SENSORS: tuple[WhoopSensorDesc, ...] = (
    # Recovery
    WhoopSensorDesc(
        key="recovery_state",
        name="Recovery State",
        icon="mdi:heart-pulse",
        value_fn=lambda d: _safe(d, "recovery", "score_state"),
    ),
    WhoopSensorDesc(
        key="recovery_score",
        name="Recovery Score",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        value_fn=lambda d: _safe(d, "recovery", "score", "recovery_score"),
        attr_fn=lambda d: _safe(d, "recovery", "score") or {},
    ),
    WhoopSensorDesc(
        key="resting_heart_rate",
        name="Resting Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart",
        value_fn=lambda d: _safe(d, "recovery", "score", "resting_heart_rate"),
    ),
    WhoopSensorDesc(
        key="hrv_rmssd",
        name="HRV (RMSSD)",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-flash",
        value_fn=lambda d: _safe(d, "recovery", "score", "hrv_rmssd_milli"),
    ),
    WhoopSensorDesc(
        key="spo2",
        name="SpO2",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:blood-bag",
        value_fn=lambda d: _safe(d, "recovery", "score", "spo2_percentage"),
    ),
    WhoopSensorDesc(
        key="skin_temp",
        name="Skin Temperature",
        native_unit_of_measurement="°C",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda d: _safe(d, "recovery", "score", "skin_temp_celsius"),
    ),
    # Sleep
    WhoopSensorDesc(
        key="sleep_state",
        name="Sleep State",
        icon="mdi:sleep",
        value_fn=lambda d: _safe(d, "sleep", "score_state"),
    ),
    WhoopSensorDesc(
        key="sleep_performance",
        name="Sleep Performance",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sleep",
        value_fn=lambda d: _safe(d, "sleep", "score", "sleep_performance_percentage"),
        attr_fn=lambda d: _safe(d, "sleep", "score") or {},
    ),
    WhoopSensorDesc(
        key="sleep_efficiency",
        name="Sleep Efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sleep",
        value_fn=lambda d: _safe(d, "sleep", "score", "sleep_efficiency_percentage"),
    ),
    WhoopSensorDesc(
        key="sleep_duration",
        name="Sleep Duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clock-outline",
        value_fn=lambda d: (
            round(ms / 60000)
            if (ms := _safe(d, "sleep", "score", "total_in_bed_time_milli"))
            else None
        ),
    ),
    WhoopSensorDesc(
        key="sleep_rem",
        name="REM Sleep",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:eye-off",
        value_fn=lambda d: (
            round(ms / 60000)
            if (ms := _safe(d, "sleep", "score", "stage_summary", "total_rem_sleep_time_milli"))
            else None
        ),
    ),
    WhoopSensorDesc(
        key="sleep_deep",
        name="Deep Sleep",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-night",
        value_fn=lambda d: (
            round(ms / 60000)
            if (ms := _safe(d, "sleep", "score", "stage_summary", "total_slow_wave_sleep_time_milli"))
            else None
        ),
    ),
    WhoopSensorDesc(
        key="respiratory_rate",
        name="Respiratory Rate",
        native_unit_of_measurement="breaths/min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lungs",
        value_fn=lambda d: _safe(d, "sleep", "score", "respiratory_rate"),
    ),
    # Workout
    WhoopSensorDesc(
        key="workout_sport",
        name="Latest Workout Sport",
        icon="mdi:run",
        value_fn=lambda d: _safe(d, "workout", "sport_name"),
    ),
    WhoopSensorDesc(
        key="workout_strain",
        name="Latest Workout Strain",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weight-lifter",
        value_fn=lambda d: _safe(d, "workout", "score", "strain"),
        attr_fn=lambda d: _safe(d, "workout", "score") or {},
    ),
    WhoopSensorDesc(
        key="workout_avg_hr",
        name="Latest Workout Avg Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-outline",
        value_fn=lambda d: _safe(d, "workout", "score", "average_heart_rate"),
    ),
    WhoopSensorDesc(
        key="workout_max_hr",
        name="Latest Workout Max Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-circle",
        value_fn=lambda d: _safe(d, "workout", "score", "max_heart_rate"),
    ),
    WhoopSensorDesc(
        key="workout_kilojoules",
        name="Latest Workout Kilojoules",
        native_unit_of_measurement="kJ",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire",
        value_fn=lambda d: _safe(d, "workout", "score", "kilojoule"),
    ),
    # Body measurement
    WhoopSensorDesc(
        key="max_heart_rate",
        name="Max Heart Rate",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-circle-outline",
        value_fn=lambda d: _safe(d, "body", "max_heart_rate"),
    ),
    WhoopSensorDesc(
        key="weight",
        name="Weight",
        native_unit_of_measurement="kg",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:scale",
        value_fn=lambda d: _safe(d, "body", "weight_kilogram"),
    ),
    WhoopSensorDesc(
        key="height",
        name="Height",
        native_unit_of_measurement="m",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:human-male-height",
        value_fn=lambda d: _safe(d, "body", "height_meter"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator_cycle: WhoopCoordinator = data[COORDINATOR_CYCLE]
    coordinator_daily: WhoopCoordinator = data[COORDINATOR_DAILY]

    entities: list[SensorEntity] = [
        WhoopSensor(coordinator_cycle, desc) for desc in CYCLE_SENSORS
    ]
    entities += [
        WhoopSensor(coordinator_daily, desc) for desc in DAILY_SENSORS
    ]
    entities += [
        WhoopLastUpdatedSensor(coordinator_cycle, "cycle"),
        WhoopLastUpdatedSensor(coordinator_daily, "daily"),
    ]
    async_add_entities(entities)


def _device_info(profile: dict | None) -> dict:
    profile = profile or {}
    user_id = profile.get("user_id", "unknown")
    name = f"Whoop ({profile.get('first_name', '')} {profile.get('last_name', '')})".strip()
    return {
        "identifiers": {(DOMAIN, str(user_id))},
        "name": name,
        "manufacturer": "Whoop",
        "model": "Whoop Band",
    }


class WhoopLastUpdatedSensor(CoordinatorEntity, SensorEntity):
    """Timestamp of the last successful data fetch."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: WhoopCoordinator, coordinator_type: str) -> None:
        super().__init__(coordinator)
        profile = _safe(coordinator.data, "profile") or {}
        user_id = profile.get("user_id", "unknown")
        self._attr_unique_id = f"whoop_{user_id}_last_updated_{coordinator_type}"
        self._attr_name = f"Last Updated ({coordinator_type.capitalize()})"
        self._attr_device_info = _device_info(profile)

    @property
    def native_value(self) -> datetime | None:
        if self.coordinator.last_update_success:
            return datetime.now(timezone.utc)
        return None


class WhoopSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: WhoopCoordinator, desc: WhoopSensorDesc) -> None:
        super().__init__(coordinator)
        self.entity_description = desc
        profile = _safe(coordinator.data, "profile") or {}
        user_id = profile.get("user_id", "unknown")
        self._attr_unique_id = f"whoop_{user_id}_{desc.key}"
        self._attr_device_info = _device_info(profile)

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        if self.coordinator.data is None:
            return {}
        return self.entity_description.attr_fn(self.coordinator.data) or {}
