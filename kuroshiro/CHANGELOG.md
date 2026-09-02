# Changelog

## [0.12.2] - 2026-09-02

### Added
- Initial release, packaging [Kuroshiro](https://github.com/PhyberApex/kuroshiro) 0.12.2 as a
  Home Assistant add-on
- Bundled PostgreSQL 17, initialised on first start and stored in `/data/postgres`, so no separate
  database add-on is needed and the data is covered by Home Assistant backups
- Device screens, firmware and plugin uploads persisted under `/data` so they survive add-on updates
- `api_url` option for the address your TRMNL devices should talk to, auto-detected from the
  Supervisor network info when left empty
