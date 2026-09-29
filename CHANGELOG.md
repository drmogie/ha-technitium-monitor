# Changelog

## 2026.09.28.01

- First release.
- Set up from the Home Assistant screen. No YAML.
- Sensors: total queries, blocked queries, blocked percent, cached,
  recursive, authoritative, server failures, clients, cache entries,
  block list size, top client, top domain, top blocked domain.
- Extra sensors, off by default: no error, not found, refused, dropped,
  zones, allowed zones, blocked zones.
- Diagnostic sensors: upstream protocol, block lists next update, server version.
- Binary sensor: ad blocking active.
- Switch: ad blocking on or off.
- Buttons: flush cache, update block lists.
- Options: how often to check, and the time span for the numbers.
- Asks for a new token if the old one stops working.
- Example dashboard in the dashboards folder.
- Tested with a fake server and the Home Assistant test tools.
  Not yet tested against a live server.
