"""Technitium Monitor: watch a Technitium DNS Server from Home Assistant."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TechnitiumClient
from .const import CONF_TOKEN, CONF_USE_SSL, CONF_VERIFY_SSL, DEFAULT_PORT
from .coordinator import TechnitiumConfigEntry, TechnitiumCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: TechnitiumConfigEntry) -> bool:
    """Set up one Technitium server."""
    verify = entry.data.get(CONF_VERIFY_SSL, True)
    client = TechnitiumClient(
        async_get_clientsession(hass, verify_ssl=verify),
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
        entry.data[CONF_TOKEN],
        entry.data.get(CONF_USE_SSL, False),
        verify,
    )
    coordinator = TechnitiumCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TechnitiumConfigEntry) -> bool:
    """Unload a server."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
