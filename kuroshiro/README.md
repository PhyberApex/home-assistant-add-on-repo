# Home Assistant Add-on: Kuroshiro

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

_Run [Kuroshiro][kuroshiro] — an open-source BYOS (Bring Your Own Server) for
[TRMNL][trmnl] e-ink displays — as a Home Assistant add-on, with PostgreSQL bundled in._

Kuroshiro bundles a NestJS API and a Vue 3 UI, and normally expects you to bring your own Postgres.
This add-on brings one along, keeps its data in `/data` so Home Assistant backs it up, and publishes
the port your TRMNL devices poll.

## Installation

1. Add this repository to Home Assistant (Settings → Add-ons → Add-on Store → ⋮ → Repositories).
2. Install the **Kuroshiro** add-on.
3. Set the `api_url` option if the auto-detected address is not the one your devices should use.
4. Start the add-on, then open it from the Home Assistant sidebar.
5. Point a TRMNL device at `http://HA-IP:3000` — devices use the port, not the sidebar.

See [DOCS.md](./DOCS.md) for configuration and the details that matter when your devices can't
reach the server.

[kuroshiro]: https://github.com/PhyberApex/kuroshiro
[trmnl]: https://usetrmnl.com/
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
