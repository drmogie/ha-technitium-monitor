"""Sensors for Technitium Monitor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import TechnitiumConfigEntry, TechnitiumData
from .entity import TechnitiumEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class TechnitiumSensorDescription(SensorEntityDescription):
    """A sensor and how to read it."""

    value_fn: Callable[[TechnitiumData], Any]
    attrs_fn: Callable[[TechnitiumData], dict[str, Any]] | None = None


def _stat(key: str) -> Callable[[TechnitiumData], Any]:
    return lambda data: data.stats.get(key)


def _blocked_percent(data: TechnitiumData) -> float | None:
    total = data.stats.get("totalQueries")
    blocked = data.stats.get("totalBlocked")
    if not total:
        return 0.0 if total == 0 else None
    return round((blocked or 0) * 100 / total, 1)


def _top_name(items: list[dict[str, Any]]) -> str | None:
    return items[0].get("name") if items else None


def _top_attrs(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"top": [{"name": i.get("name"), "hits": i.get("hits")} for i in items[:10]]}


def _next_update(data: TechnitiumData) -> datetime | None:
    raw = data.settings.get("blockListNextUpdatedOn")
    if not raw:
        return None
    try:
        parsed = dt_util.parse_datetime(str(raw))
    except (ValueError, TypeError):
        return None
    if parsed is None or parsed.year < 2000:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt_util.UTC)


def _count(key: str, icon: str, *, default: bool = True) -> TechnitiumSensorDescription:
    return TechnitiumSensorDescription(
        key=key,
        translation_key=key,
        icon=icon,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=default,
        value_fn=_stat(key),
    )


SENSORS: tuple[TechnitiumSensorDescription, ...] = (
    _count("totalQueries", "mdi:dns"),
    _count("totalBlocked", "mdi:shield-off"),
    TechnitiumSensorDescription(
        key="blockedPercent",
        translation_key="blockedPercent",
        icon="mdi:shield-half-full",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_blocked_percent,
    ),
    _count("totalCached", "mdi:database-clock"),
    _count("totalRecursive", "mdi:earth"),
    _count("totalAuthoritative", "mdi:book-lock"),
    _count("totalNoError", "mdi:check-circle-outline", default=False),
    _count("totalNxDomain", "mdi:help-circle-outline", default=False),
    _count("totalServerFailure", "mdi:alert-circle-outline"),
    _count("totalRefused", "mdi:cancel", default=False),
    _count("totalDropped", "mdi:tray-remove", default=False),
    _count("totalClients", "mdi:devices"),
    _count("zones", "mdi:folder-network", default=False),
    _count("cachedEntries", "mdi:database"),
    _count("blockListZones", "mdi:playlist-remove"),
    _count("allowedZones", "mdi:playlist-check", default=False),
    _count("blockedZones", "mdi:playlist-minus", default=False),
    TechnitiumSensorDescription(
        key="topClient",
        translation_key="topClient",
        icon="mdi:account-network",
        value_fn=lambda d: _top_name(d.top_clients),
        attrs_fn=lambda d: _top_attrs(d.top_clients),
    ),
    TechnitiumSensorDescription(
        key="topDomain",
        translation_key="topDomain",
        icon="mdi:web",
        value_fn=lambda d: _top_name(d.top_domains),
        attrs_fn=lambda d: _top_attrs(d.top_domains),
    ),
    TechnitiumSensorDescription(
        key="topBlockedDomain",
        translation_key="topBlockedDomain",
        icon="mdi:web-cancel",
        value_fn=lambda d: _top_name(d.top_blocked_domains),
        attrs_fn=lambda d: _top_attrs(d.top_blocked_domains),
    ),
    TechnitiumSensorDescription(
        key="upstream",
        translation_key="upstream",
        icon="mdi:lock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.settings.get("forwarderProtocol"),
        attrs_fn=lambda d: {"forwarders": d.settings.get("forwarders")},
    ),
    TechnitiumSensorDescription(
        key="blockListNextUpdate",
        translation_key="blockListNextUpdate",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_next_update,
    ),
    TechnitiumSensorDescription(
        key="version",
        translation_key="version",
        icon="mdi:tag-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.settings.get("version"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors."""
    coordinator = entry.runtime_data
    async_add_entities(TechnitiumSensor(coordinator, d) for d in SENSORS)


class TechnitiumSensor(TechnitiumEntity, SensorEntity):
    """One number or text from the server."""

    entity_description: TechnitiumSensorDescription

    def __init__(self, coordinator, description: TechnitiumSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fn = self.entity_description.attrs_fn
        return fn(self.coordinator.data) if fn else None
