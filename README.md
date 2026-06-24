# Nova

Nova is a homemade, privacy-focused smart assistant box for a Raspberry Pi 4. It starts as a typed-command assistant that works on a Mac or regular computer, then can grow into a voice assistant with eSpeak NG, a WS2812B LED ring, microphone wake word, weather, search, Spotify, alarms, timers, notes, and family accounts.

Nova is designed to be safe for a kid/family project:

- It does not save random room audio.
- It stores only useful local data like settings, users, alarms, timers, notes, and privacy mode.
- API keys live in `.env.local`, not in code.
- Missing hardware and missing API keys do not crash the app.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full Nova master architecture, feature rules, hardware plan, data flow, and roadmap.

## Planned Hardware

- Raspberry Pi 4
- microSD card
- USB microphone or mic module
- Speaker or small speaker system
- WS2812B LED ring, about 48 mm outside diameter
- Transparent PLA diffuser ring
- 3D printed square case and top lid
- Jumper wires
- 330 ohm to 470 ohm resistor for the LED data wire
- Screws or hardware

The LED ring is the main status light. No extra status LEDs are required.

## Install On Raspberry Pi

```bash
sudo apt update
sudo apt install -y espeak-ng python3-pip python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.local
python main.py
```

## Install On Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.local
python main.py
```

Optional eSpeak NG on Mac:

```bash
brew install espeak-ng
```

If eSpeak NG is missing, Nova still works and prints what it would say.

## Run Nova

```bash
python main.py
```

Try:

```text
hello
help
what time is it
status report
system check
math 5 + 7
math sqrt(81)
solve x**2 - 5*x + 6 = 0
spell minerals
define field
search what is a resistor
weather
tell me a joke
set a timer for 10 seconds
list timers
set an alarm for 9:45 AM
list alarms
go private
go private for 10 minutes
stop listening until 9 AM
quiz mode
party mode
calm mode
good morning mode
exit
```

## JokeStack

Nova's joke system works offline with local jokes, stores per-user joke history in `data/joke_history.json`, tracks usage counts, and avoids telling the same user the same joke twice in a row when possible.

Future upgrades can add online joke fetching, ratings, favorites, and most-used joke summaries without changing the command flow.

## LED Ring

By default, hardware LEDs are disabled so Nova works on a Mac.

In `.env.local`:

```env
NOVA_LED_ENABLED=true
NOVA_LED_COUNT=12
NOVA_LED_PIN=18
NOVA_LED_BRIGHTNESS=80
```

Nova tries to use `rpi_ws281x` on Raspberry Pi. If that package or the hardware is missing, Nova falls back to printing messages like:

```text
[LED] blue listening
```

Using GPIO18/PWM for real WS2812B LEDs may require running with `sudo` on Raspberry Pi.

Optional hardware packages for later:

```bash
pip install rpi_ws281x adafruit-circuitpython-neopixel RPi.GPIO
```

## OLED Display

Nova supports the UCTRONICS 0.96 inch 128x64 yellow/blue SSD1306 I2C OLED display. Hardware is disabled by default so Nova still runs on a Mac or without the screen attached.

Raspberry Pi wiring:

| OLED pin | Raspberry Pi physical pin | Raspberry Pi GPIO name |
| --- | --- | --- |
| GND | Pin 6 | Ground |
| VCC | Pin 1 | 3.3V |
| SCL | Pin 5 | GPIO3 / SCL1 |
| SDA | Pin 3 | GPIO2 / SDA1 |

Use 3.3V for Nova's Raspberry Pi build. The product supports 3.3V-5V, but 3.3V keeps the I2C signals Pi-safe.

Enable I2C on Raspberry Pi:

```bash
sudo raspi-config
```

Then choose `Interface Options` -> `I2C` -> `Enable`.

Optional OLED packages on Raspberry Pi:

```bash
pip install adafruit-circuitpython-ssd1306 pillow
```

In `.env.local`:

```env
NOVA_OLED_ENABLED=true
NOVA_OLED_WIDTH=128
NOVA_OLED_HEIGHT=64
NOVA_OLED_I2C_ADDRESS=60
```

`60` is decimal for the common `0x3C` SSD1306 I2C address. If `i2cdetect -y 1` shows `3d`, use `NOVA_OLED_I2C_ADDRESS=61`.

If the OLED screen, I2C bus, or Python display libraries are missing, Nova prints messages like:

```text
[OLED] Ready | Awaiting command
```

## API Keys

All keys go in `.env.local`.

Weather uses OpenWeather:

```env
OPENWEATHER_API_KEY=your_key_here
```

Google search uses Programmable Search Engine:

```env
GOOGLE_API_KEY=your_key_here
GOOGLE_SEARCH_ENGINE_ID=your_engine_id_here
```

Spotify needs a Developer app and may require Spotify Premium for playback control:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8080/callback
```

If keys are missing, Nova gives a friendly setup message.

## System Check

Run from inside Nova:

```text
system check
```

Or:

```bash
python main.py --system-check
```

It checks voice fallback, LED fallback/hardware, storage files, API config, and current time.

## Privacy Notes

- Nova does not save microphone recordings by default.
- Typed commands are not saved as audio.
- Web/API calls only happen when you ask for weather, search, dictionary, Spotify, or another online feature.
- Privacy mode can be started with `go private`, `go private for 10 minutes`, or `stop listening until 9 AM`.
- In privacy mode, Nova blocks normal commands and keeps only privacy status commands available.

## Raspberry Pi Notes

- Use a resistor around 330 ohm to 470 ohm on the WS2812B data line.
- Use a power setup appropriate for your LED ring.
- GPIO18/PWM is common for WS2812B examples.
- Real microphone and wake-word support are intentionally placeholders in the MVP so typed commands work first.
