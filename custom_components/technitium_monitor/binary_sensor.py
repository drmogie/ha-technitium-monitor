"""Binary sensor for Technitium Monitor."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import TechnitiumConfigEntry
from .entity import TechnitiumEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the binary sensors."""
    async_add_entities([TechnitiumBlockingSensor(entry.runtime_data)])


class TechnitiumBlockingSensor(TechnitiumEntity, BinarySensorEntity):
    """On when ad blocking is turned on."""

    _attr_translation_key = "blocking"
    _attr_icon = "mdi:shield-check"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "blocking")

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.settings.get("enableBlocking")
        return None if value is None else bool(value)
