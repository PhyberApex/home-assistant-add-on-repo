# Changelog

## [2.1.0] - 2026-07-25

### Added
- CPU temperature reading (`/sys/class/thermal/thermal_zone0/temp`), shown compactly on the
  standard info screen and as a large centered reading in always-on mode
- `enable_button` config option (default `true`) to run without a physical GPIO20 button
- Always-on display mode (used automatically when `enable_button: false`), cycling the info
  screen and a big temperature screen with no sleep timeout
- Opt-in fan control (`enable_fan_control`, `fan_temp_on`, `fan_temp_off`) for PoE HATs with a
  PCF8574 I2C fan controller at `0x20` (e.g. Waveshare PoE HAT (B)), based on the protocol used
  by [raspi-poe-mon](https://github.com/klamann/raspi-poe-mon) and
  [RustBerry-PoE-Monitor](https://github.com/jackra1n/RustBerry-PoE-Monitor)
- `flip_display` option for the two supported orientations (0°/180°)
- Per-stat visibility options: `show_hostname`, `show_ip`, `show_cpu`, `show_memory`, `show_temperature`

### Fixed
- Boards with no button/pull-up wired to GPIO20 (e.g. Waveshare PoE HAT (B)) could have the pin
  float and be misread as a sustained button press, walking through the reboot/shutdown hold
  timers and unintentionally rebooting or shutting down the host shortly after startup. Setting
  `enable_button: false` now prevents GPIO20 from ever being requested, eliminating this risk.

## [2.0.2] - 2025-02-04

### Fixed
- Linting issues

## [2.0.0] - 2025-02-04

### Removed
- Removed deprecated architectures

## [1.0.1] - 2025-02-04

### Added
- Logo and icon

### Fixed
- Linting issues

## [1.0.0] - 2025-02-03

### Added
- Initial release
- Support for SSD1306 OLED display (128x32)
- System information display (IP, hostname, CPU, memory)
- GPIO button control
- Reboot functionality (long press ~8 seconds)
- Shutdown functionality (long press ~12 seconds)
- LED indicator support
- Auto-start on boot