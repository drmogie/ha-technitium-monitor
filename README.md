# Technitium Monitor

[![HACS Custom][hacs-badge]][hacs-url]
![Version](https://img.shields.io/badge/version-2026.09.28.01-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Watch and control a [Technitium DNS Server](https://technitium.com/dns/)
from Home Assistant. Set up from the screen. No YAML.

## What you get

**Sensors**

- Total queries, blocked queries, blocked percent
- Cached, recursive and authoritative answers
- Server failures, clients, cache entries
- Block list size
- Top client, top domain, top blocked domain (the top 10 are in the attributes)
- Off by default: no error, not found, refused, dropped, zones,
  allowed zones, blocked zones
- Diagnostics: upstream protocol, block lists next update, server version

**Controls**

- Switch: ad blocking on or off for the whole network
- Button: flush cache
- Button: update block lists

The numbers cover the last day. You can change that in the options.

## Install with HACS

1. HACS, three-dot menu, **Custom repositories**.
2. Add `https://github.com/drmogie/ha-technitium-monitor`, type **Integration**.
3. Download **Technitium Monitor** and restart Home Assistant.

## Set up

1. In the Technitium web page, click your user name (top right).
2. Click **Create API Token**. Give it a name. Copy the token.
3. In Home Assistant: Settings, Devices and services, **Add integration**,
   **Technitium Monitor**.
4. Enter the host, port (5380), and the token.

If the server runs on the Home Assistant computer, use its IP address.
Do not use `localhost`.

## Options

Settings, Devices and services, Technitium Monitor, **Configure**.

- Check every (seconds): 15 to 3600. Default 60.
- Time span for the numbers: last hour, day, week or month.

## Dashboard

`dashboards/technitium-monitor.yaml` is a ready dashboard.
Open your dashboard, three dots, **Raw configuration editor**, and paste
the views in. Or make a new dashboard and paste the whole file.
It assumes the server was added as `192.168.1.10`. If yours is different,
replace `technitium_192_168_1_10` in the file.

## Good to know

- The token is stored by Home Assistant, like any other integration.
  Use a token from a user that has the rights you want.
  A read-only user can watch but cannot use the switch or buttons.
- Turning the switch off turns ad blocking off until you turn it on again.
- If the token stops working, Home Assistant asks you for a new one.

## Test

```
pip install pytest-homeassistant-custom-component
pytest
```

## License

MIT. See [LICENSE](LICENSE).
Technitium DNS Server is made by
[Technitium](https://github.com/TechnitiumSoftware/DnsServer).
This project is not made by or endorsed by Technitium.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz
