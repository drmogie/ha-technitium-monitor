"""Constants for Technitium Monitor."""

from __future__ import annotations

DOMAIN = "technitium_monitor"

CONF_TOKEN = "api_token"
CONF_USE_SSL = "use_ssl"
CONF_VERIFY_SSL = "verify_ssl"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_PERIOD = "period"

DEFAULT_PORT = 5380
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 15
MAX_SCAN_INTERVAL = 3600
DEFAULT_PERIOD = "LastDay"
PERIODS = ["LastHour", "LastDay", "LastWeek", "LastMonth"]
