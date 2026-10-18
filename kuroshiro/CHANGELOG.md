# Changelog

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
