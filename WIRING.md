# Nova Wiring Guide

This guide describes the current Nova Raspberry Pi wiring plan. It uses Nova's centralized GPIO settings from `.env.local`:

```text
# 🍓 Hardware GPIO Pin Assignments
```

Pin naming used here:

- `GPIO` or `BCM` means the Raspberry Pi GPIO number.
- `Physical pin` means the numbered position on the 40-pin Raspberry Pi header.
- `D17`, `D23`, and similar names are CircuitPython-style board aliases for Raspberry Pi GPIO pins.

## Safety Rules

- Power off the Raspberry Pi before changing wiring.
- Use 3.3V logic for Raspberry Pi GPIO pins.
- Do not connect a 5V signal directly into a Raspberry Pi GPIO input.
- Use a common ground between Nova, sensors, LED power, and supporting boards.
- The Raspberry Pi has no built-in analog input. Analog voltage sensors need an ADC module before connecting to the Pi.

## Current GPIO Summary

| Nova setting | Current value | GPIO / bus name | Physical pin | Used by |
| --- | ---: | --- | ---: | --- |
| `NOVA_GPIO_OLED_SDA_PIN` | `D2` | GPIO2 / SDA1 | Pin 3 | OLED I2C data |
| `NOVA_GPIO_OLED_SCL_PIN` | `D3` | GPIO3 / SCL1 | Pin 5 | OLED I2C clock |
| `NOVA_GPIO_OLED_I2C_ADDRESS` | `60` | I2C address `0x3C` | N/A | OLED address |
| `NOVA_GPIO_LED_RING_PIN` | `18` | GPIO18 / PWM0 | Pin 12 | LED ring data |
| `NOVA_GPIO_ROTARY_CLK_PIN` | `D5` | GPIO5 | Pin 29 | Rotary encoder CLK |
| `NOVA_GPIO_ROTARY_DT_PIN` | `D6` | GPIO6 | Pin 31 | Rotary encoder DT |
| `NOVA_GPIO_ROTARY_SW_PIN` | blank | Not assigned | N/A | Rotary encoder push button |
| `NOVA_GPIO_DHT22_PIN` | `D17` | GPIO17 | Pin 11 | DHT22 data |
| `NOVA_GPIO_PIR_PIN` | `D23` | GPIO23 | Pin 16 | PIR motion signal |
| `NOVA_GPIO_ULTRASONIC_TRIGGER_PIN` | `D24` | GPIO24 | Pin 18 | Ultrasonic trigger |
| `NOVA_GPIO_ULTRASONIC_ECHO_PIN` | `D25` | GPIO25 | Pin 22 | Ultrasonic echo |
| `NOVA_GPIO_BH1750_SDA_PIN` | `D2` | GPIO2 / SDA1 | Pin 3 | BH1750 I2C data |
| `NOVA_GPIO_BH1750_SCL_PIN` | `D3` | GPIO3 / SCL1 | Pin 5 | BH1750 I2C clock |
| `NOVA_GPIO_BH1750_I2C_ADDRESS` | `35` | I2C address `0x23` | N/A | BH1750 address |
| `NOVA_GPIO_CAMERA_CONNECTOR` | `CSI` | Camera ribbon connector | CSI port | Camera module |

## Raspberry Pi Power Pins Used

| Power rail | Physical pin options | Notes |
| --- | --- | --- |
| 3.3V | Pin 1 or Pin 17 | Use for OLED, BH1750, DHT22, PIR output modules, and rotary encoder logic. |
| 5V | Pin 2 or Pin 4 | Use only for devices that require 5V power. Do not feed 5V signal into GPIO. |
| Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 | All modules should share ground with the Pi. |

## OLED Display

Nova currently supports a 128x64 SSD1306 I2C OLED.

| OLED pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `VCC` | 3.3V | Pin 1 or Pin 17 |
| `GND` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |
| `SCL` | GPIO3 / SCL1 / `D3` | Pin 5 |
| `SDA` | GPIO2 / SDA1 / `D2` | Pin 3 |

Current config:

```env
NOVA_GPIO_OLED_SDA_PIN=D2
NOVA_GPIO_OLED_SCL_PIN=D3
NOVA_GPIO_OLED_I2C_ADDRESS=60
```

`60` is decimal for I2C address `0x3C`.

## BH1750 Light Sensor

The BH1750 uses the same I2C bus as the OLED.

| BH1750 pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `VCC` | 3.3V | Pin 1 or Pin 17 |
| `GND` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |
| `SCL` | GPIO3 / SCL1 / `D3` | Pin 5 |
| `SDA` | GPIO2 / SDA1 / `D2` | Pin 3 |
| `ADDR` | Optional | Leave disconnected for address `0x23` on most modules. |

Current config:

```env
NOVA_GPIO_BH1750_SDA_PIN=D2
NOVA_GPIO_BH1750_SCL_PIN=D3
NOVA_GPIO_BH1750_I2C_ADDRESS=35
```

`35` is decimal for I2C address `0x23`.

## DHT22 Temperature and Humidity Sensor

| DHT22 pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `VCC` / `+` | 3.3V | Pin 1 or Pin 17 |
| `DATA` / `OUT` | GPIO17 / `D17` | Pin 11 |
| `GND` / `-` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |

Current config:

```env
NOVA_GPIO_DHT22_PIN=D17
```

If using a bare 4-pin DHT22, add a 10k pull-up resistor between `VCC` and `DATA`. Many 3-pin modules already include this resistor.

## LED Ring

Nova's current LED ring setting uses GPIO18, which is commonly used for WS2812B/NeoPixel data.

| LED ring pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `DIN` / data input | GPIO18 / PWM0 | Pin 12 |
| `GND` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |
| `5V` / `VCC` | External 5V recommended | Do not overload the Pi 5V pin. |

Current config:

```env
NOVA_GPIO_LED_RING_PIN=18
```

Notes:

- Use a common ground between the LED ring power supply and Raspberry Pi.
- A level shifter from 3.3V data to 5V data is recommended for reliable LEDs.
- A resistor around 330-470 ohms in series with the data line is commonly used.
- A capacitor across LED power and ground is commonly used for larger LED strips/rings.

## Rotary Encoder Volume Dial

The rotary encoder currently uses GPIO5 and GPIO6 for rotation. The push button is supported by Nova but is not assigned in the current local config.

| Encoder pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `CLK` | GPIO5 / `D5` | Pin 29 |
| `DT` | GPIO6 / `D6` | Pin 31 |
| `SW` | Not assigned | N/A |
| `+` / `VCC` | 3.3V | Pin 1 or Pin 17 |
| `GND` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |

Current config:

```env
NOVA_GPIO_ROTARY_CLK_PIN=D5
NOVA_GPIO_ROTARY_DT_PIN=D6
NOVA_GPIO_ROTARY_SW_PIN=
```

If you want to enable the built-in push button for mute/unmute, choose an unused GPIO pin and set `NOVA_GPIO_ROTARY_SW_PIN`. A reasonable future option is GPIO16 / `D16` / physical pin 36, if it is not being used by another device.

## PIR Motion Sensor

| PIR pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `VCC` | 3.3V or 5V, depending on module | Pin 1/17 for 3.3V or Pin 2/4 for 5V |
| `OUT` | GPIO23 / `D23` | Pin 16 |
| `GND` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |

Current config:

```env
NOVA_GPIO_PIR_PIN=D23
```

Important: confirm the PIR module's `OUT` signal is 3.3V-safe before connecting it to GPIO23.

## Ultrasonic Distance Sensor

Many HC-SR04-style ultrasonic sensors use 5V logic. The Raspberry Pi echo input must be reduced to 3.3V with a voltage divider or level shifter.

| Ultrasonic pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `VCC` | 5V | Pin 2 or Pin 4 |
| `TRIG` | GPIO24 / `D24` | Pin 18 |
| `ECHO` | GPIO25 / `D25` through level shifting | Pin 22 |
| `GND` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |

Current config:

```env
NOVA_GPIO_ULTRASONIC_TRIGGER_PIN=D24
NOVA_GPIO_ULTRASONIC_ECHO_PIN=D25
```

Do not wire a 5V echo signal directly to the Raspberry Pi.

## Camera Module

The Raspberry Pi camera module uses the CSI ribbon connector, not the 40-pin GPIO header.

| Camera connection | Raspberry Pi location |
| --- | --- |
| Ribbon cable | CSI camera connector |

Current config:

```env
NOVA_GPIO_CAMERA_CONNECTOR=CSI
```

## Voltage Sensor

Nova has software placeholders for voltage sensing, but Raspberry Pi GPIO pins cannot read analog voltage directly.

Use an ADC module, such as an ADS1115, between the voltage sensor and Raspberry Pi. The ADS1115 usually connects over I2C.

| ADC pin | Raspberry Pi pin name | Physical pin |
| --- | --- | ---: |
| `VDD` | 3.3V | Pin 1 or Pin 17 |
| `GND` | Ground | Pin 6, 9, 14, 20, 25, 30, 34, or 39 |
| `SCL` | GPIO3 / SCL1 / `D3` | Pin 5 |
| `SDA` | GPIO2 / SDA1 / `D2` | Pin 3 |
| Analog input | ADC channel | Not a Pi GPIO pin |

Do not connect an analog voltage sensor output directly to a Raspberry Pi GPIO pin.

## Speakers

Nova's current speaker support is software/audio-output based, not GPIO based.

Common options:

| Speaker option | Raspberry Pi connection |
| --- | --- |
| HDMI audio | HDMI port |
| USB speaker or USB audio adapter | USB port |
| 3.5mm audio, on supported Pi models | 3.5mm jack |
| Future I2S amplifier | Requires a separate pin plan before wiring |

Avoid reusing GPIO18 for I2S audio while it is assigned to the LED ring.

## Mini Breadboard

Use the breadboard for shared power rails and signal organization.

Recommended layout:

- One rail for 3.3V.
- One rail for ground.
- Keep 5V rails clearly separate from 3.3V rails.
- Label I2C lines `SDA` and `SCL`.
- Keep the ultrasonic `ECHO` level shifting close to the sensor or breadboard.

## Future GPIO Placeholders

These are reserved in config but are not wired yet:

```env
NOVA_GPIO_FUTURE_BUTTON_1_PIN=
NOVA_GPIO_FUTURE_BUTTON_2_PIN=
NOVA_GPIO_FUTURE_BUZZER_PIN=
NOVA_GPIO_FUTURE_RELAY_1_PIN=
NOVA_GPIO_FUTURE_SENSOR_1_PIN=
```

Before assigning future hardware, check for conflicts with existing pins.

## Pin Conflict Checklist

Current assigned GPIO pins:

- GPIO2 / physical pin 3: I2C SDA for OLED and BH1750.
- GPIO3 / physical pin 5: I2C SCL for OLED and BH1750.
- GPIO5 / physical pin 29: Rotary encoder CLK.
- GPIO6 / physical pin 31: Rotary encoder DT.
- GPIO17 / physical pin 11: DHT22 data.
- GPIO18 / physical pin 12: LED ring data.
- GPIO23 / physical pin 16: PIR motion signal.
- GPIO24 / physical pin 18: Ultrasonic trigger.
- GPIO25 / physical pin 22: Ultrasonic echo.

Unassigned but planned:

- Rotary encoder `SW` mute button.
- Voltage sensor ADC channel.
- Future buttons, buzzer, relays, and extra sensors.
