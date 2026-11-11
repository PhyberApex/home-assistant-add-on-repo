# Changelog

## [0.23.0] - 2026-11-11

### Changed
- Packages [Kuroshiro](https://github.com/PhyberApex/kuroshiro) 0.23.0 (was 0.20.0). See the
  [upstream releases](https://github.com/PhyberApex/kuroshiro/releases) for what changed in
  Kuroshiro itself; the add-on's wiring (bundled Postgres, `/data` layout, `api_url`) is unchanged,
  so existing installs update in place.
- Kuroshiro no longer runs as root. The add-on still starts as root, because it has a Postgres
  cluster to bring up, and hands `/data/screens/devices` and `/data/firmware` to the `node` user on
  the first start before dropping to it. Nothing to do by hand, and the ownership change survives a
  restore of an older backup.
- Chromium renders without its sandbox here. A Home Assistant add-on cannot pass the seccomp
  profile the sandbox needs, so Kuroshiro falls back to `--no-sandbox` - unprivileged now, where it
  used to be root.

### Added
- The Recipe Gallery: browse, search and sort trmnl.com's published Recipes from inside Kuroshiro
  and import one in a click, instead of pasting a Recipe id.
- A `/health` probe reporting process and database status.
- Manual Rotation, a Dithering switch, per-model official Firmware sync with "Catch up now", Alert
  reminders, and a long list of Plugin and Data Source improvements from 0.21.0.

## [0.20.0] - 2026-10-18

### Changed
- Packages [Kuroshiro](https://github.com/PhyberApex/kuroshiro) 0.20.0 (was 0.12.2). See the
  [upstream releases](https://github.com/PhyberApex/kuroshiro/releases) for what changed in
  Kuroshiro itself; the add-on's wiring (bundled Postgres, `/data` layout, `api_url`) is unchanged,
  so existing installs update in place.
- Backups are taken cold. Home Assistant stops the add-on before copying `/data`, so the bundled
  Postgres cluster is never snapshotted mid-write.
- Plugin and recipe uploads are no longer persisted under `/data/uploads`. Kuroshiro holds uploads
  in memory now, and Housekeeping offers to clear the folder left behind by older versions.

## [0.12.2.1] - 2026-09-02

### Fixed
- Migrations failed on a fresh install with `extension "uuid-ossp" is not available`. Alpine ships
  the contrib extensions separately from the server, so `postgresql17-contrib` is now installed
  alongside it. Existing installs recover on restart - the failed migration rolled back, so no data
  is lost and nothing needs wiping.

## [0.12.2] - 2026-09-02

### Added
- Initial release, packaging [Kuroshiro](https://github.com/PhyberApex/kuroshiro) 0.12.2 as a
  Home Assistant add-on. The add-on version tracks the Kuroshiro version it packages.
- Bundled PostgreSQL 17, initialised on first start and stored in `/data/postgres`, so no separate
  database add-on is needed and the data is covered by Home Assistant backups
- Device screens, firmware and plugin uploads persisted under `/data` so they survive add-on updates
- `api_url` option for the address your TRMNL devices should talk to, auto-detected from the
  Supervisor network info when left empty
- Ingress panel, so the web UI opens from the Home Assistant sidebar, alongside the published port
  that TRMNL devices poll
