"""Data update coordinator for Technitium Monitor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TechnitiumAuthError,
    TechnitiumClient,
    TechnitiumConnectionError,
    TechnitiumError,
)
from .const import (
    CONF_PERIOD,
    CONF_SCAN_INTERVAL,
    DEFAULT_PERIOD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

type TechnitiumConfigEntry = ConfigEntry[TechnitiumCoordinator]


@dataclass
class TechnitiumData:
    """One fetch from the server."""

    stats: dict[str, Any] = field(default_factory=dict)
    top_clients: list[dict[str, Any]] = field(default_factory=list)
    top_domains: list[dict[str, Any]] = field(default_factory=list)
    top_blocked_domains: list[dict[str, Any]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)


class TechnitiumCoordinator(DataUpdateCoordinator[TechnitiumData]):
    """Fetches stats and settings on a timer."""

    config_entry: TechnitiumConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: TechnitiumConfigEntry,
        client: TechnitiumClient,
    ) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client
        self.period: str = entry.options.get(CONF_PERIOD, DEFAULT_PERIOD)

    async def _async_update_data(self) -> TechnitiumData:
        try:
            stats_doc = await self.client.async_get_stats(self.period)
            settings = await self.client.async_get_settings()
        except TechnitiumAuthError as err:
            raise ConfigEntryAuthFailed("The API token is not valid") from err
        except TechnitiumConnectionError as err:
            raise UpdateFailed(f"Cannot reach the server: {err}") from err
        except TechnitiumError as err:
            raise UpdateFailed(str(err)) from err

        return TechnitiumData(
            stats=stats_doc.get("stats", {}) or {},
            top_clients=stats_doc.get("topClients", []) or [],
            top_domains=stats_doc.get("topDomains", []) or [],
            top_blocked_domains=stats_doc.get("topBlockedDomains", []) or [],
            settings=settings or {},
        )
