#!/usr/bin/env python3
"""
OLED System Info Display
Displays system information on SSD1306 OLED with GPIO button control
Uses gpiod and smbus2 for container compatibility
"""

import time
import subprocess
import os
import sys
from collections import namedtuple
import gpiod
from smbus2 import SMBus, i2c_msg
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import psutil
import requests


StatsConfig = namedtuple("StatsConfig", ["hostname", "ip", "cpu", "memory", "temperature"])
FanConfig = namedtuple("FanConfig", ["enabled", "temp_on", "temp_off"])

THERMAL_ZONE_PATH = '/sys/class/thermal/thermal_zone0/temp'

FAN_I2C_ADDR = 0x20
FAN_PIN_MASK = 0x01  # P0 on the PCF8574 IO-expander, active-low


def log(message):
    """Print log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def env_bool(name, default):
    """Parse a bashio-exported bool env var ('true'/'false')"""
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() == "true"


def supervisor_api(endpoint):
    """Call Home Assistant Supervisor API"""
    try:
        response = requests.get(
            f'http://supervisor/{endpoint}',
            headers={'Authorization': f'Bearer {os.getenv("SUPERVISOR_TOKEN")}'},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log(f"API Error ({endpoint}): {e}")
    return None


class I2CAdapter:
    """SMBus adapter for Adafruit CircuitPython libraries"""

    def __init__(self, bus_number=1):
        self.bus = SMBus(bus_number)
        self._locked = False

    def try_lock(self):
        if not self._locked:
            self._locked = True
            return True
        return False

    def unlock(self):
        self._locked = False

    def writeto(self, address, buffer, *, start=0, end=None):
        if end is None:
            end = len(buffer)

        length = end - start
        if length == 0:
            try:
                self.bus.read_byte(address)
            except:
                pass
            return

        data = bytes(buffer[start:end])
        msg = i2c_msg.write(address, data)
        self.bus.i2c_rdwr(msg)

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        if end is None:
            end = len(buffer)

        length = end - start
        msg = i2c_msg.read(address, length)
        self.bus.i2c_rdwr(msg)

        for i, byte in enumerate(msg):
            buffer[start + i] = byte


def reboot_system():
    """Reboot Home Assistant via Supervisor API"""
    log("REBOOT: Triggering system reboot via Supervisor API")
    try:
        response = requests.post('http://supervisor/host/reboot',
                                headers={'Authorization': f'Bearer {os.getenv("SUPERVISOR_TOKEN")}'})
        log(f"REBOOT: Response status: {response.status_code}")
    except Exception as e:
        log(f"REBOOT: Error - {e}")


def shutdown_system():
    """Shutdown Home Assistant via Supervisor API"""
    log("SHUTDOWN: Triggering system shutdown via Supervisor API")
    try:
        response = requests.post('http://supervisor/host/shutdown',
                                headers={'Authorization': f'Bearer {os.getenv("SUPERVISOR_TOKEN")}'})
        log(f"SHUTDOWN: Response status: {response.status_code}")
    except Exception as e:
        log(f"SHUTDOWN: Error - {e}")


def get_cpu_temperature():
    """Read CPU temperature (°C) from the host thermal zone.

    /sys/class/thermal is not namespaced by Docker's default sysfs mount
    (unlike most of /proc), so this reflects the real host temperature with
    no extra device/volume mounts required. Returns None if unreadable.
    """
    try:
        with open(THERMAL_ZONE_PATH, 'r') as f:
            raw = f.read().strip()
        return int(raw) / 1000.0
    except (OSError, ValueError):
        return None


def get_system_info():
    """Retrieve HOST system information via Supervisor API"""
    # Get host info
    host_info = supervisor_api('host/info')
    network_info = supervisor_api('network/info')
    os_info = supervisor_api('os/info')

    # Hostname
    if host_info and 'data' in host_info:
        hostname = host_info['data'].get('hostname', 'unknown')
    else:
        hostname = subprocess.check_output("hostname", shell=True).decode('UTF-8').strip()

    # IP address - try to get primary network interface
    ip = "0.0.0.0"
    if network_info and 'data' in network_info:
        interfaces = network_info['data'].get('interfaces', [])
        for iface in interfaces:
            if iface.get('primary', False) and iface.get('ipv4'):
                ip = iface['ipv4'].get('address', ['0.0.0.0'])[0].split('/')[0]
                break
        # Fallback to first interface with an IP
        if ip == "0.0.0.0":
            for iface in interfaces:
                if iface.get('ipv4') and iface['ipv4'].get('address'):
                    ip = iface['ipv4']['address'][0].split('/')[0]
                    if not ip.startswith('172.'):  # Skip docker networks
                        break

    if ip == "0.0.0.0":
        try:
            ip = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True).decode('UTF-8').strip()
        except:
            pass

    # CPU and Memory - use host /proc if mounted, otherwise container stats
    try:
        # Try to read from host /proc
        if os.path.exists('/host/proc/stat'):
            # We'd need to parse /proc/stat manually - complex
            # For now, fall back to psutil on container
            cpu = f"{psutil.cpu_percent():3.0f}"
        else:
            cpu = f"{psutil.cpu_percent():3.0f}"
    except:
        cpu = "N/A"

    try:
        # Try to read from host /proc/meminfo
        if os.path.exists('/host/proc/meminfo'):
            with open('/host/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = int(parts[1].strip().split()[0])

                total = meminfo.get('MemTotal', 0)
                available = meminfo.get('MemAvailable', 0)
                if total > 0:
                    used_percent = ((total - available) / total) * 100
                    mem = f"{used_percent:2.0f}"
                else:
                    mem = f"{psutil.virtual_memory().percent:2.0f}"
        else:
            mem = f"{psutil.virtual_memory().percent:2.0f}"
    except:
        mem = "N/A"

    temp_c = get_cpu_temperature()
    temp = f"{temp_c:.0f}" if temp_c is not None else "--"

    return hostname, ip, cpu, mem, temp


def draw_info_screen(draw, x, top, font, hostname, ip, cpu, mem, temp, stats_cfg):
    """Render the hostname/IP/CPU+MEM+temp info screen into `draw`"""
    if stats_cfg.hostname:
        draw.text((x, top), f"NAME: {hostname}", font=font, fill=255)
    if stats_cfg.ip:
        draw.text((x, top + 12), f"IP  : {ip}", font=font, fill=255)

    parts = []
    if stats_cfg.cpu:
        parts.append(f"CPU:{cpu.strip()}%")
    if stats_cfg.memory:
        parts.append(f"MEM:{mem.strip()}%")
    if stats_cfg.temperature:
        parts.append(f"{temp}C")
    if parts:
        draw.text((x, top + 24), " ".join(parts), font=font, fill=255)


def draw_big_temp_screen(draw, disp, big_font, small_font, temp_c, fan_on):
    """Render a large, centered CPU temperature reading, with an optional
    small fan status line, into `draw`"""
    text = f"{temp_c:.0f}°C" if temp_c is not None else "N/A"
    bbox = draw.textbbox((0, 0), text, font=big_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    status = f"FAN {'ON' if fan_on else 'OFF'}" if fan_on is not None else None
    sbbox = None
    sh = 0
    if status:
        sbbox = draw.textbbox((0, 0), status, font=small_font)
        sh = sbbox[3] - sbbox[1]

    total_h = th + (sh + 2 if status else 0)
    ty = max(0, (disp.height - total_h) // 2)

    tx = (disp.width - tw) // 2 - bbox[0]
    draw.text((tx, ty - bbox[1]), text, font=big_font, fill=255)

    if status:
        sw = sbbox[2] - sbbox[0]
        sx = (disp.width - sw) // 2 - sbbox[0]
        sy = ty + th + 2
        draw.text((sx, sy - sbbox[1]), status, font=small_font, fill=255)


def fan_read_raw(bus):
    """Read the PCF8574 IO-expander output byte, or None if no device responds"""
    try:
        return bus.read_byte(FAN_I2C_ADDR)
    except OSError:
        return None


def fan_apply(bus, turn_on):
    """Set the fan (PCF8574 P0, active-low), preserving the other expander bits"""
    current = fan_read_raw(bus)
    if current is None:
        return
    if turn_on:
        new_value = current & ~FAN_PIN_MASK & 0xFF
    else:
        new_value = current | FAN_PIN_MASK
    bus.write_byte(FAN_I2C_ADDR, new_value)


def compute_fan_desired(current_on, temp_c, temp_on, temp_off):
    """Hysteresis: turn on at temp_on, off at temp_off, hold state otherwise"""
    if temp_c is None:
        return current_on
    if not current_on and temp_c >= temp_on:
        return True
    if current_on and temp_c <= temp_off:
        return False
    return current_on


def fan_tick(bus, current_on, temp_c, temp_on, temp_off):
    """Update fan state for one tick; only touches hardware on an actual change"""
    desired = compute_fan_desired(current_on, temp_c, temp_on, temp_off)
    if desired != current_on:
        fan_apply(bus, desired)
        temp_note = f" (CPU {temp_c:.0f}C)" if temp_c is not None else ""
        log(f"FAN: turned {'ON' if desired else 'OFF'}{temp_note}")
    return desired


def run_button_loop(disp, image, draw, font, btn_line, i2c_bus, fan_on, fan_cfg, stats_cfg, x, top):
    """Button-driven mode: press to wake the display, hold to reboot/shutdown"""
    disp_timer = 0
    menu_timer = 0
    menu_state = 0
    last_button_state = 1

    DISP_TIMEOUT = 15
    REBOOT_TIMEOUT = 5
    SHUTDOWN_TIMEOUT = 10

    log("Entering main loop")

    while True:
        draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

        button_state = btn_line.get_value()

        if button_state != last_button_state:
            if button_state == 0:
                log("BUTTON: Pressed")
            else:
                log(f"BUTTON: Released (menu_timer={menu_timer}, menu_state={menu_state})")
            last_button_state = button_state

        if button_state == 0:
            if menu_timer == 0:
                log("Display activated")

            if menu_timer == REBOOT_TIMEOUT:
                log("MENU: Entering REBOOT state")
                menu_state = 1

            if menu_timer == SHUTDOWN_TIMEOUT:
                log("MENU: Entering SHUTDOWN state")
                menu_state = 2

            disp_timer = DISP_TIMEOUT
            menu_timer += 1
        elif disp_timer == 0:
            disp.image(image)
            disp.show()

        if disp_timer > 0:
            if menu_state == 0:
                hostname, ip, cpu, mem, temp = get_system_info()
                draw_info_screen(draw, x, top, font, hostname, ip, cpu, mem, temp, stats_cfg)
                disp_timer -= 1

                if disp_timer == 0:
                    log("Display timeout - entering sleep mode")

                if button_state == 1:
                    if menu_timer > 0:
                        log("MENU: Reset to INFO state")
                    menu_timer = 0
                    menu_state = 0

            elif menu_state == 1:
                if button_state == 1:
                    draw.text((x, top+12), "Performing Reboot...", font=font, fill=255)
                    disp.image(image)
                    disp.show()
                    time.sleep(3)
                    reboot_system()
                else:
                    draw.text((x, top),    ".......Reboot.......", font=font, fill=255)
                    draw.text((x, top+12), "   Release Button   ", font=font, fill=255)
                    draw.text((x, top+24), "      To Reboot     ", font=font, fill=255)

            elif menu_state == 2:
                if button_state == 1:
                    draw.text((x, top+12), "Shutting down.......", font=font, fill=255)
                    disp.image(image)
                    disp.show()
                    time.sleep(3)
                    shutdown_system()
                else:
                    draw.text((x, top),    "......Shutdown......", font=font, fill=255)
                    draw.text((x, top+12), "   Release Button   ", font=font, fill=255)
                    draw.text((x, top+24), "    To Shutdown     ", font=font, fill=255)

            disp.image(image)
            disp.show()

        if fan_cfg.enabled:
            fan_on = fan_tick(i2c_bus, fan_on, get_cpu_temperature(), fan_cfg.temp_on, fan_cfg.temp_off)

        time.sleep(1)


def run_always_on_loop(disp, image, draw, font, big_font, i2c_bus, fan_on, fan_cfg, stats_cfg, x, top):
    """Always-on mode (no button): cycles the info screen and a big temperature
    screen every PAGE_SECONDS, with no sleep timeout and no reboot/shutdown"""
    PAGE_SECONDS = 5

    log("Entering always-on display loop (button disabled)")

    page_timer = 0
    show_temp_page = False

    while True:
        temp_c = get_cpu_temperature()

        if fan_cfg.enabled:
            fan_on = fan_tick(i2c_bus, fan_on, temp_c, fan_cfg.temp_on, fan_cfg.temp_off)

        draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

        if show_temp_page and stats_cfg.temperature:
            draw_big_temp_screen(draw, disp, big_font, font, temp_c, fan_on if fan_cfg.enabled else None)
        else:
            hostname, ip, cpu, mem, temp = get_system_info()
            draw_info_screen(draw, x, top, font, hostname, ip, cpu, mem, temp, stats_cfg)

        disp.image(image)
        disp.show()

        page_timer += 1
        if page_timer >= PAGE_SECONDS:
            page_timer = 0
            if stats_cfg.temperature:
                show_temp_page = not show_temp_page

        time.sleep(1)


def main():
    log("Initializing OLED System Info Display")

    enable_button = env_bool("ENABLE_BUTTON", True)
    enable_fan_control = env_bool("ENABLE_FAN_CONTROL", False)
    fan_temp_on = int(os.getenv("FAN_TEMP_ON", "60"))
    fan_temp_off = int(os.getenv("FAN_TEMP_OFF", "50"))
    flip_display = env_bool("FLIP_DISPLAY", True)
    stats_cfg = StatsConfig(
        hostname=env_bool("SHOW_HOSTNAME", True),
        ip=env_bool("SHOW_IP", True),
        cpu=env_bool("SHOW_CPU", True),
        memory=env_bool("SHOW_MEMORY", True),
        temperature=env_bool("SHOW_TEMPERATURE", True),
    )

    # GPIO configuration
    LED = 23
    INFO_BTN = 20

    log(f"Configuring GPIO - LED: GPIO{LED}" + (f", Button: GPIO{INFO_BTN}" if enable_button else ""))
    chip = gpiod.Chip('gpiochip0')
    led_line = chip.get_line(LED)
    led_line.request(consumer="oled-display", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

    btn_line = None
    if enable_button:
        btn_line = chip.get_line(INFO_BTN)
        btn_line.request(consumer="oled-display", type=gpiod.LINE_REQ_DIR_IN)
    else:
        log("Button support disabled (enable_button=false) - GPIO20 will not be requested; running in always-on mode")
    log("GPIO configured successfully")

    # Display configuration
    log("Initializing I2C and OLED display")
    i2c = I2CAdapter(1)
    disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
    disp.rotation = 2 if flip_display else 0
    disp.fill(0)
    disp.show()
    log("OLED display initialized")

    # Drawing setup
    image = Image.new("1", (disp.width, disp.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    big_font = ImageFont.load_default(size=28)

    # Display constants
    padding = -2
    x = 0
    top = padding

    temp_probe = get_cpu_temperature()
    if temp_probe is None:
        log(f"WARNING: CPU temperature sensor not found at {THERMAL_ZONE_PATH}")
    else:
        log(f"CPU temperature sensor OK ({temp_probe:.0f}C)")

    fan_on = False
    if enable_fan_control:
        if fan_temp_on <= fan_temp_off:
            log(f"WARNING: fan_temp_on ({fan_temp_on}) must be greater than fan_temp_off "
                f"({fan_temp_off}) - disabling fan control")
            enable_fan_control = False
        else:
            fan_probe = fan_read_raw(i2c.bus)
            if fan_probe is None:
                log(f"WARNING: No I2C device found at 0x{FAN_I2C_ADDR:02x} - disabling fan control")
                enable_fan_control = False
            else:
                fan_on = (fan_probe & FAN_PIN_MASK) == 0
                log(f"Fan control enabled (on={fan_temp_on}C, off={fan_temp_off}C) - "
                    f"currently {'ON' if fan_on else 'OFF'}")

    fan_cfg = FanConfig(enabled=enable_fan_control, temp_on=fan_temp_on, temp_off=fan_temp_off)

    # Turn on LED
    led_line.set_value(1)
    log("Status LED turned on")

    # Startup message
    log("Displaying startup message")
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)
    draw.text((x, top),    "--------------------", font=font, fill=255)
    draw.text((x, top+12), " Infoscreen Started ", font=font, fill=255)
    draw.text((x, top+24), "--------------------", font=font, fill=255)
    disp.image(image)
    disp.show()
    time.sleep(5)

    try:
        if enable_button:
            run_button_loop(disp, image, draw, font, btn_line, i2c.bus, fan_on, fan_cfg, stats_cfg, x, top)
        else:
            run_always_on_loop(disp, image, draw, font, big_font, i2c.bus, fan_on, fan_cfg, stats_cfg, x, top)
    except KeyboardInterrupt:
        log("Received keyboard interrupt")
    except Exception as e:
        log(f"ERROR: {e}")
        raise
    finally:
        log("Cleaning up GPIO resources")
        led_line.release()
        if btn_line is not None:
            btn_line.release()
        log("Shutdown complete")


if __name__ == "__main__":
    main()
