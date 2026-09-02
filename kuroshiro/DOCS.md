# Home Assistant Add-on: Kuroshiro

## Installation

1. Add this add-on repository to Home Assistant.
2. Install the **Kuroshiro** add-on.
3. Review the `api_url` option below.
4. Start the add-on and watch the log — the first start initialises the database, which takes a
   few seconds longer than later ones.

## Configuration

### Option: `api_url`

The address your **TRMNL devices** use to reach this server, for example
`http://192.168.1.10:3000`.

This matters more than it looks. Kuroshiro hands each device absolute URLs for the images and
firmware it should fetch, and it builds them from this value. If it is wrong, the web UI will look
fine while your devices show nothing.

Leave it empty to have the add-on ask the Supervisor for your Home Assistant host's IP address and
use `http://<that-ip>:3000`. Set it explicitly when:

- you changed the published port from the default `3000`,
- your Home Assistant host has several network interfaces and the wrong one gets picked,
- you reach Kuroshiro through a reverse proxy or a hostname instead of an IP.

The add-on refuses to start if it cannot determine an address, rather than starting with a broken
one.

## Ports

| Port       | Purpose                                                                    |
| ---------- | -------------------------------------------------------------------------- |
| `3000/tcp` | The web UI, **and** the API your TRMNL devices poll. Devices need this port |

The UI is also available through the Home Assistant sidebar (ingress). Devices cannot use ingress —
they are not Home Assistant clients and have no session — so the published port has to stay
reachable on your network for them to work.

> **Known limitation:** the sidebar panel currently loads and then fails its API calls, because
> Kuroshiro's UI requests absolute `/api/...` paths that ingress's prefix breaks. This is tracked
> upstream in [PhyberApex/kuroshiro#908][ingress-issue]. Until that ships, use
> `http://<your-ha-ip>:3000` directly. The published port is unaffected either way.

## Data and backups

Everything that matters lives under the add-on's `/data` directory, so it is included in Home
Assistant backups and survives add-on updates:

| Path                | Contents                                       |
| ------------------- | ---------------------------------------------- |
| `/data/postgres`    | The bundled PostgreSQL cluster                 |
| `/data/screens`     | Rendered device screens and their originals    |
| `/data/firmware`    | Synced and custom-uploaded firmware images     |
| `/data/uploads`     | Temporary files from plugin and recipe imports |

Uninstalling the add-on deletes all of it. Take a backup first if you want to keep it.

## The database

PostgreSQL runs inside the add-on and listens on loopback only, inside the add-on's own network
namespace — it is not reachable from your network and needs no password management from you. There
is nothing to configure, and no separate database add-on to install.

## Alpha software

Kuroshiro is still in alpha and not feature complete. Breaking changes happen, and an update may
require wiping data and starting fresh. See the [upstream README][kuroshiro] before relying on it
for anything you care about.

[kuroshiro]: https://github.com/PhyberApex/kuroshiro
[ingress-issue]: https://github.com/PhyberApex/kuroshiro/issues/908
