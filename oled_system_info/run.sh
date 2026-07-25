#!/usr/bin/with-contenv bashio

bashio::log.info "Starting OLED System Info Display..."

if [ ! -e "/dev/i2c-1" ]; then
    bashio::log.error "I2C device /dev/i2c-1 not found!"
    exit 1
fi

if [ ! -e "/dev/gpiochip0" ]; then
    bashio::log.error "GPIO chip device /dev/gpiochip0 not found!"
    exit 1
fi

bashio::log.info "Scanning I2C bus..."
i2cdetect -y 1

BOARD_TYPE=$(bashio::config 'board_type')
CHIP_TYPE=$(bashio::config 'chip_type')

export BLINKA_FORCEBOARD="${BOARD_TYPE}"
export BLINKA_FORCECHIP="${CHIP_TYPE}"

export ENABLE_BUTTON=$(bashio::config 'enable_button')
export ENABLE_FAN_CONTROL=$(bashio::config 'enable_fan_control')
export FAN_TEMP_ON=$(bashio::config 'fan_temp_on')
export FAN_TEMP_OFF=$(bashio::config 'fan_temp_off')
export FLIP_DISPLAY=$(bashio::config 'flip_display')
export SHOW_HOSTNAME=$(bashio::config 'show_hostname')
export SHOW_IP=$(bashio::config 'show_ip')
export SHOW_CPU=$(bashio::config 'show_cpu')
export SHOW_MEMORY=$(bashio::config 'show_memory')
export SHOW_TEMPERATURE=$(bashio::config 'show_temperature')

bashio::log.info "Board: ${BOARD_TYPE}, Chip: ${CHIP_TYPE}, Button: ${ENABLE_BUTTON}, Fan control: ${ENABLE_FAN_CONTROL}"
bashio::log.info "Starting OLED display script..."

python3 /system_info.py