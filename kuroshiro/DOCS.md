# Home Assistant Add-on: Kuroshiro

## Installation

1. Add this add-on repository to Home Assistant.
2. Install the **Kuroshiro** add-on.
3. Review the `api_url` option below, and `render_allowed_hosts` if a Screen of yours renders from
   a service on your network.
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

### Option: `render_allowed_hosts`

Hosts on your network a Screen's Template may fetch from, as host names, IP addresses or CIDR
ranges. Empty by default, which means none.

A Plugin's Template is third-party code — most of it imported from the Recipe Gallery — and
Kuroshiro runs it with JavaScript on in its own browser on every render. So it refuses every
private address and internal host name a Template asks for, and this option is where you name the
exceptions:

```yaml
render_allowed_hosts:
  - homeassistant.local
  - 192.168.1.0/24
```

Set it when a Template of yours reads from a service on your network — your Home Assistant
instance, a NAS, a local weather station. A host named by name may be reached at whatever address
it currently resolves to; a range is matched against the addresses themselves.

Nothing you list here can reach Kuroshiro's own admin API, which is refused before this option is
consulted. `0.0.0.0/0` and `::/0` together allow your whole network, if you would rather make that
choice once and be done with it.

A Template whose host is not listed sees the fetch fail as a network error, so a Screen that used
to draw data from your LAN comes up blank until you add its host here.

## Ports

| Port       | Purpose                                                                    |
| ---------- | -------------------------------------------------------------------------- |
| `3000/tcp` | The web UI, **and** the API your TRMNL devices poll. Devices need this port |

The UI also opens straight from the Home Assistant sidebar through ingress, which is the easiest way
to use it day to day.

The published port still has to stay reachable on your network, because **devices cannot use
ingress** — they are not Home Assistant clients and have no session. Kuroshiro hands each device
absolute image and firmware URLs built from `api_url`, and those always point at the port. The UI
remains available directly at `http://HA-IP:3000` too.

## Data and backups

Everything that matters lives under the add-on's `/data` directory, so it is included in Home
Assistant backups and survives add-on updates:

| Path                | Contents                                       |
| ------------------- | ---------------------------------------------- |
| `/data/postgres`    | The bundled PostgreSQL cluster                 |
| `/data/screens`     | Rendered device screens and their originals    |
| `/data/firmware`    | Synced and custom-uploaded firmware images     |

Uninstalling the add-on deletes all of it. Take a backup first if you want to keep it.

## The database

PostgreSQL runs inside the add-on and listens on loopback only, inside the add-on's own network
namespace — it is not reachable from your network and needs no password management from you. There
is nothing to configure, and no separate database add-on to install.

## Alpha software

Kuroshiro is still in alpha and not feature complete. Breaking changes happen, and an update may
require wiping data and starting fresh. See the [upstream README][kuroshiro] before relying on it
for anything you care about.

[kuroshiro]: https://github.com/usetrmnl/kuroshiro
