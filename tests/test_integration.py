"""Tests for Technitium Monitor, using a fake HTTP layer."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.technitium_monitor.const import (
    CONF_TOKEN,
    CONF_USE_SSL,
    CONF_VERIFY_SSL,
    DOMAIN,
)

BASE = "http://192.168.1.10:5380"
DATA = {
    CONF_HOST: "192.168.1.10",
    CONF_PORT: 5380,
    CONF_TOKEN: "secret-token",
    CONF_USE_SSL: False,
    CONF_VERIFY_SSL: True,
}

STATS = {
    "status": "ok",
    "response": {
        "stats": {
            "totalQueries": 200, "totalBlocked": 50, "totalCached": 20, "totalRecursive": 100,
            "totalAuthoritative": 30, "totalNoError": 150, "totalNxDomain": 40,
            "totalServerFailure": 1, "totalRefused": 0, "totalDropped": 0, "totalClients": 7,
            "zones": 2, "cachedEntries": 178, "allowedZones": 0, "blockedZones": 0,
            "allowListZones": 0, "blockListZones": 74760,
        },
        "topClients": [{"name": "192.168.1.137", "hits": 99}, {"name": "192.168.1.205", "hits": 10}],
        "topDomains": [{"name": "google.com", "hits": 30}],
        "topBlockedDomains": [{"name": "doubleclick.net", "hits": 12}],
    },
}
SETTINGS = {
    "status": "ok",
    "response": {
        "version": "15.5.1",
        "enableBlocking": True,
        "forwarderProtocol": "Https",
        "forwarders": ["https://cloudflare-dns.com/dns-query"],
        "blockListNextUpdatedOn": "2026-09-30T01:07:34.4011804Z",
    },
}


def mock_server(mocker: AiohttpClientMocker, settings=SETTINGS, stats=STATS) -> None:
    mocker.get(f"{BASE}/api/dashboard/stats/get", json=stats)
    mocker.get(f"{BASE}/api/settings/get", json=settings)
    mocker.get(f"{BASE}/api/settings/set", json={"status": "ok", "response": {}})
    mocker.get(f"{BASE}/api/cache/flush", json={"status": "ok"})
    mocker.get(f"{BASE}/api/settings/forceUpdateBlockLists", json={"status": "ok"})


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, unique_id="192.168.1.10:5380", title="Technitium (192.168.1.10)")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow_ok(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_server(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Technitium (192.168.1.10)"
    assert result["data"][CONF_TOKEN] == "secret-token"


async def test_config_flow_bad_token(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{BASE}/api/settings/get", json={"status": "invalid-token"})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_config_flow_cannot_connect(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    import aiohttp
    aioclient_mock.get(f"{BASE}/api/settings/get", exc=aiohttp.ClientError("nope"))
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["errors"] == {"base": "cannot_connect"}


async def test_config_flow_duplicate(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_server(aioclient_mock)
    await _setup(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_sensors(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_server(aioclient_mock)
    await _setup(hass)
    assert hass.states.get("sensor.technitium_192_168_1_10_total_queries").state == "200"
    assert hass.states.get("sensor.technitium_192_168_1_10_blocked_queries").state == "50"
    assert hass.states.get("sensor.technitium_192_168_1_10_blocked_percent").state == "25.0"
    assert hass.states.get("sensor.technitium_192_168_1_10_block_list_domains").state == "74760"
    top = hass.states.get("sensor.technitium_192_168_1_10_top_blocked_domain")
    assert top.state == "doubleclick.net"
    assert top.attributes["top"][0]["hits"] == 12
    assert hass.states.get("sensor.technitium_192_168_1_10_top_client").state == "192.168.1.137"
    assert hass.states.get("sensor.technitium_192_168_1_10_upstream_protocol").state == "Https"
    assert hass.states.get("sensor.technitium_192_168_1_10_server_version").state == "15.5.1"
    nxt = hass.states.get("sensor.technitium_192_168_1_10_block_lists_next_update")
    assert nxt.state.startswith("2026-09-30T01:07:34")
    assert hass.states.get("binary_sensor.technitium_192_168_1_10_ad_blocking_active").state == STATE_ON
    assert hass.states.get("switch.technitium_192_168_1_10_ad_blocking").state == STATE_ON


async def test_zero_queries_and_unset_date(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    stats = {"status": "ok", "response": {"stats": {"totalQueries": 0, "totalBlocked": 0}}}
    settings = {"status": "ok", "response": {"version": "15", "enableBlocking": False,
                                              "blockListNextUpdatedOn": "0001-01-02T00:00:00"}}
    mock_server(aioclient_mock, settings, stats)
    await _setup(hass)
    assert hass.states.get("sensor.technitium_192_168_1_10_blocked_percent").state == "0.0"
    assert hass.states.get("sensor.technitium_192_168_1_10_block_lists_next_update").state == "unknown"
    assert hass.states.get("sensor.technitium_192_168_1_10_top_client").state == "unknown"
    assert hass.states.get("switch.technitium_192_168_1_10_ad_blocking").state == STATE_OFF


async def test_switch_and_buttons(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_server(aioclient_mock)
    await _setup(hass)
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.technitium_192_168_1_10_ad_blocking"}, blocking=True)
    calls = [c for c in aioclient_mock.mock_calls if "/api/settings/set" in str(c[1])]
    assert calls and "enableBlocking=false" in str(calls[-1][1])
    await hass.services.async_call("button", "press", {"entity_id": "button.technitium_192_168_1_10_flush_cache"}, blocking=True)
    await hass.services.async_call("button", "press", {"entity_id": "button.technitium_192_168_1_10_update_block_lists"}, blocking=True)
    seen = " ".join(str(c[1]) for c in aioclient_mock.mock_calls)
    assert "/api/cache/flush" in seen and "forceUpdateBlockLists" in seen


async def test_token_sent_as_bearer_only(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_server(aioclient_mock)
    await _setup(hass)
    for method, url, data, headers in aioclient_mock.mock_calls:
        assert headers["Authorization"] == "Bearer secret-token"
        assert "secret-token" not in str(url)


async def test_auth_failure_starts_reauth(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{BASE}/api/dashboard/stats/get", json={"status": "invalid-token"})
    aioclient_mock.get(f"{BASE}/api/settings/get", json={"status": "invalid-token"})
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, unique_id="192.168.1.10:5380", title="Technitium (192.168.1.10)")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.SETUP_ERROR
    assert any(f["context"]["source"] == "reauth" for f in hass.config_entries.flow.async_progress())


async def test_unload(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_server(aioclient_mock)
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED


async def test_options_flow(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_server(aioclient_mock)
    entry = await _setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 30, "period": "LastWeek"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options == {"scan_interval": 30, "period": "LastWeek"}
    assert any("type=LastWeek" in str(c[1]) for c in aioclient_mock.mock_calls)
