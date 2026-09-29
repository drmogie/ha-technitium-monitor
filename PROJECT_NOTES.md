# Project notes

Technitium Monitor: a Home Assistant integration for a Technitium DNS Server.
Repo `ha-technitium-monitor`, domain `technitium_monitor`.

## 2026.09.28.01 (built 2026-09-28)

- Asked for by Mogie: "build in some HA tool and build a page on HA-Blue
  for monitoring technitium". Chose: build our own integration (not a
  community one), build and release, then ask before touching ha-blue.
- Name chosen from a question: ha-technitium-monitor.
- Talks to the server with the same API the technitium-mcp tool uses
  (`/api/dashboard/stats/get`, `/api/settings/get`, `/api/settings/set`,
  `/api/cache/flush`, `/api/settings/forceUpdateBlockLists`), Bearer token.
- `api.py` has no Home Assistant imports.
- Home Assistant has no built-in Technitium integration (checked
  ha-blue: no entry, only the add-on's update entity).
- Tested with pytest-homeassistant-custom-component on Python 3.13 with
  Home Assistant 2026.2.3 (the newest that installs on the test machine).
  The cloud test machine could not run Python 3.14 with that version.
- Not tested on a live server or live Home Assistant.
- Dashboard example: `dashboards/technitium-monitor.yaml`.
- Entity ids come from the device name `Technitium (<host>)`.
