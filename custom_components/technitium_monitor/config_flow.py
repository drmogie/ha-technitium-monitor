"""Config flow for Technitium Monitor."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    TechnitiumAuthError,
    TechnitiumClient,
    TechnitiumConnectionError,
    TechnitiumError,
)
from .const import (
    CONF_PERIOD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USE_SSL,
    CONF_VERIFY_SSL,
    DEFAULT_PERIOD,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    PERIODS,
)
from .coordinator import TechnitiumConfigEntry

_LOGGER = logging.getLogger(__name__)

TOKEN_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


async def _validate(hass, data: Mapping[str, Any]) -> dict[str, str]:
    """Try the settings. Returns an error dict (empty when fine)."""
    verify = data.get(CONF_VERIFY_SSL, True)
    client = TechnitiumClient(
        async_get_clientsession(hass, verify_ssl=verify),
        data[CONF_HOST],
        data.get(CONF_PORT, DEFAULT_PORT),
        data[CONF_TOKEN],
        data.get(CONF_USE_SSL, False),
        verify,
    )
    try:
        await client.async_get_settings()
    except TechnitiumAuthError:
        return {"base": "invalid_auth"}
    except TechnitiumConnectionError:
        return {"base": "cannot_connect"}
    except TechnitiumError:
        return {"base": "unknown"}
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error while checking the server")
        return {"base": "unknown"}
    return {}


class TechnitiumConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up a Technitium server from the screen."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            user_input = {**user_input, CONF_HOST: host}
            await self.async_set_unique_id(f"{host}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            errors = await _validate(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title=f"Technitium ({host})", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_TOKEN): TOKEN_SELECTOR,
                vol.Required(CONF_USE_SSL, default=False): bool,
                vol.Required(CONF_VERIFY_SSL, default=True): bool,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            errors = await _validate(self.hass, {**entry.data, CONF_TOKEN: user_input[CONF_TOKEN]})
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_TOKEN: user_input[CONF_TOKEN]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): TOKEN_SELECTOR}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: TechnitiumConfigEntry) -> TechnitiumOptionsFlow:
        return TechnitiumOptionsFlow()


class TechnitiumOptionsFlow(OptionsFlowWithReload):
    """How often to check, and which time span the numbers cover."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
                vol.Required(CONF_PERIOD, default=DEFAULT_PERIOD): SelectSelector(
                    SelectSelectorConfig(options=PERIODS, translation_key="period")
                ),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, self.config_entry.options),
        )
