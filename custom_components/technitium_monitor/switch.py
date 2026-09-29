"""Ad blocking switch for Technitium Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import TechnitiumError
from .coordinator import TechnitiumConfigEntry
from .entity import TechnitiumEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the switch."""
    async_add_entities([TechnitiumBlockingSwitch(entry.runtime_data)])


class TechnitiumBlockingSwitch(TechnitiumEntity, SwitchEntity):
    """Turn ad blocking on or off for the whole network."""

    _attr_translation_key = "blocking_switch"
    _attr_icon = "mdi:shield"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "blocking_switch")

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.settings.get("enableBlocking")
        return None if value is None else bool(value)

    async def _set(self, enabled: bool) -> None:
        try:
            await self.coordinator.client.async_set_blocking(enabled)
        except TechnitiumError as err:
            raise HomeAssistantError(f"Could not change ad blocking: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
