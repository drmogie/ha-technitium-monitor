"""Buttons for Technitium Monitor."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import TechnitiumClient, TechnitiumError
from .coordinator import TechnitiumConfigEntry
from .entity import TechnitiumEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class TechnitiumButtonDescription(ButtonEntityDescription):
    """A button and the call it makes."""

    press_fn: Callable[[TechnitiumClient], Awaitable[None]]


BUTTONS: tuple[TechnitiumButtonDescription, ...] = (
    TechnitiumButtonDescription(
        key="flush_cache",
        translation_key="flush_cache",
        icon="mdi:database-remove",
        press_fn=lambda c: c.async_flush_cache(),
    ),
    TechnitiumButtonDescription(
        key="update_block_lists",
        translation_key="update_block_lists",
        icon="mdi:cloud-refresh",
        press_fn=lambda c: c.async_update_block_lists(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TechnitiumConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the buttons."""
    async_add_entities(TechnitiumButton(entry.runtime_data, d) for d in BUTTONS)


class TechnitiumButton(TechnitiumEntity, ButtonEntity):
    """Runs one action on the server."""

    entity_description: TechnitiumButtonDescription

    def __init__(self, coordinator, description: TechnitiumButtonDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        try:
            await self.entity_description.press_fn(self.coordinator.client)
        except TechnitiumError as err:
            raise HomeAssistantError(f"The server said no: {err}") from err
        await self.coordinator.async_request_refresh()
