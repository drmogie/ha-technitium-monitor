"""Small async client for the Technitium DNS Server HTTP API.

This file does not import Home Assistant, so it can be tested on its own.
"""

from __future__ import annotations

from typing import Any

import aiohttp


class TechnitiumError(Exception):
    """Base error."""


class TechnitiumConnectionError(TechnitiumError):
    """The server could not be reached."""


class TechnitiumAuthError(TechnitiumError):
    """The API token is not valid."""


class TechnitiumApiError(TechnitiumError):
    """The server answered with an error."""


class TechnitiumClient:
    """Talks to one Technitium DNS Server."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        token: str,
        use_ssl: bool = False,
        verify_ssl: bool = True,
    ) -> None:
        scheme = "https" if use_ssl else "http"
        host = host.strip()
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"  # bare IPv6 address
        self._base = f"{scheme}://{host}:{port}"
        self._session = session
        self._token = token
        self._ssl: bool | None = None if verify_ssl else False

    @property
    def base_url(self) -> str:
        """Web address of the server."""
        return self._base

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in (params or {}).items()}
        try:
            async with self._session.get(
                f"{self._base}{path}",
                params=query,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=15),
                ssl=self._ssl,
            ) as resp:
                if resp.status in (401, 403):
                    raise TechnitiumAuthError("The server refused the token")
                if resp.status != 200:
                    raise TechnitiumApiError(f"HTTP {resp.status}")
                doc = await resp.json(content_type=None)
        except TechnitiumError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise TechnitiumConnectionError(str(err)) from err
        except ValueError as err:
            raise TechnitiumApiError("The server sent something that is not JSON") from err

        if not isinstance(doc, dict):
            raise TechnitiumApiError("Unexpected answer from the server")
        status = doc.get("status")
        if status == "ok":
            return doc.get("response", {})
        if status in ("invalid-token", "2fa-required"):
            raise TechnitiumAuthError(status)
        raise TechnitiumApiError(str(doc.get("errorMessage", status)))

    async def async_get_stats(self, period: str) -> dict[str, Any]:
        """Dashboard numbers and top lists."""
        return await self._get("/api/dashboard/stats/get", {"type": period})

    async def async_get_settings(self) -> dict[str, Any]:
        """Server settings."""
        return await self._get("/api/settings/get")

    async def async_set_blocking(self, enabled: bool) -> None:
        """Turn ad blocking on or off."""
        await self._get("/api/settings/set", {"enableBlocking": enabled})

    async def async_flush_cache(self) -> None:
        """Clear the DNS cache."""
        await self._get("/api/cache/flush")

    async def async_update_block_lists(self) -> None:
        """Download the block lists again now."""
        await self._get("/api/settings/forceUpdateBlockLists")
