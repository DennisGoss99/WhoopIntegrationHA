"""Whoop sensors — daily metrics + live heart rate."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

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

from .const import COORDINATOR_DAILY, COORDINATOR_HR, DOMAIN
from . import WhoopCoordinator


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe(data: dict | None, *keys: str) -> Any:
    """Traverse nested keys safely, returning None if any key is missing."""
    node = data
    for k in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(k)
    return node


# ── sensor descriptions ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class WhoopSensorDesc(SensorEntityDescription):
    value_fn: Callable[[dict], Any] = field(default=lambda _: None)
    attr_fn: Callable[[dict], dict] = field(default=lambda _: {})


DAILY_SENSORS: tuple[WhoopSensorDesc, ...] = (
    # Recovery
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
        key="hrv_rmssd",
        name="HRV (RMSSD)",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-flash",
        value_fn=lambda d: _safe(d, "recovery", "score", "hrv_rmssd_milli"),
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
    # Cycle / Strain
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
    # Workout
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
)


# ── platform setup ────────────────────────────────────────────────────────────

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator_daily: WhoopCoordinator = data[COORDINATOR_DAILY]
    coordinator_hr: WhoopCoordinator = data[COORDINATOR_HR]

    entities: list[SensorEntity] = [
        WhoopDailySensor(coordinator_daily, desc) for desc in DAILY_SENSORS
    ]
    entities.append(WhoopHeartRateSensor(coordinator_hr, coordinator_daily))

    async_add_entities(entities)


# ── sensor entities ───────────────────────────────────────────────────────────

def _device_info(profile: dict | None) -> dict:
    if not profile:
        profile = {}
    user_id = profile.get("user_id", "unknown")
    first = profile.get("first_name", "")
    last = profile.get("last_name", "")
    return {
        "identifiers": {(DOMAIN, str(user_id))},
        "name": f"Whoop ({first} {last})".strip(),
        "manufacturer": "Whoop",
        "model": "Whoop Band",
    }


class WhoopDailySensor(CoordinatorEntity, SensorEntity):
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


class WhoopHeartRateSensor(CoordinatorEntity, SensorEntity):
    """Live heart rate sensor — updates every 60 seconds."""

    _attr_has_entity_name = True
    _attr_name = "Heart Rate"
    _attr_native_unit_of_measurement = "bpm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:heart-pulse"

    def __init__(
        self,
        coordinator_hr: WhoopCoordinator,
        coordinator_daily: WhoopCoordinator,
    ) -> None:
        super().__init__(coordinator_hr)
        self._coordinator_daily = coordinator_daily
        profile = _safe(coordinator_daily.data, "profile") or {}
        user_id = profile.get("user_id", "unknown")
        self._attr_unique_id = f"whoop_{user_id}_heart_rate_live"
        self._attr_device_info = _device_info(profile)

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data
