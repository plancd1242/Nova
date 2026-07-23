# Nova

Nova is a homemade, privacy-focused smart assistant box for a Raspberry Pi 3B+. It starts as a typed-command assistant that works on a Mac or regular computer, then can grow into a voice assistant with eSpeak NG, a WS2812B LED ring, microphone wake word, weather, search, Spotify, alarms, timers, notes, and family accounts.

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
- DIYmall 16 LED WS2812B RGB ring, using one ring from the pack
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
NOVA_LED_COUNT=16
NOVA_GPIO_LED_RING_PIN=18
NOVA_LED_BRIGHTNESS=80
```

Nova tries to use `rpi_ws281x` on Raspberry Pi. The DIYmall ring is a 5V WS2812B/5050 individually-addressable RGB ring, so this driver is the correct software family. If that package or the hardware is missing, Nova falls back to printing messages like:

```text
[LED] blue listening
```

Using GPIO18/PWM for real WS2812B LEDs may require elevated mailbox/GPIO access on Raspberry Pi. If `python main.py` shows `Failed to create mailbox device`, run Nova with the project virtualenv under sudo:

```bash
sudo .venv/bin/python main.py
```

Avoid `sudo python main.py` unless root's Python has all Nova dependencies installed.

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
NOVA_GPIO_OLED_I2C_ADDRESS=60
NOVA_OLED_REFRESH_SECONDS=5
```

`60` is decimal for the common `0x3C` SSD1306 I2C address. If `i2cdetect -y 1` shows `3d`, use `NOVA_GPIO_OLED_I2C_ADDRESS=61`.

Nova refreshes the OLED automatically while it is running, so the clock and sensor readings keep updating even when no command is being entered. `NOVA_OLED_REFRESH_SECONDS=5` is a good default for the DHT22 because the sensor should not be polled too aggressively.

If the OLED screen, I2C bus, or Python display libraries are missing, Nova prints messages like:

```text
[OLED] Ready | Awaiting command
```

## Temperature And Humidity Sensor

Nova supports a DHT22/AM2302 temperature and humidity sensor. Hardware is disabled by default so Nova can still run without the sensor attached.

Raspberry Pi wiring:

| Sensor pin | Raspberry Pi physical pin | Raspberry Pi GPIO name |
| --- | --- | --- |
| VCC / + | Pin 1 | 3.3V |
| DATA / OUT | Pin 11 | GPIO17 |
| GND / - | Pin 9 | Ground |

If your sensor is the bare 4-pin DHT22 instead of a 3-pin module, add a 10k pull-up resistor between VCC and DATA. Many 3-pin breakout modules already include this resistor.

Optional sensor package on Raspberry Pi:

```bash
pip install adafruit-circuitpython-dht
```

In `.env.local`:

```env
NOVA_CLIMATE_ENABLED=true
NOVA_CLIMATE_SENSOR_TYPE=DHT22
NOVA_GPIO_DHT22_PIN=D17
```

With the OLED enabled, Nova shows room temperature and humidity on ready, waiting, thinking, and done screens. You can also ask:

```text
room temperature
temperature
humidity
climate
```

## OLED Dashboard

Nova's OLED dashboard keeps the existing status API and adds a small pixel Nova face, time, room temperature, humidity, Wi-Fi signal status, voltage, light level, and current operating mode. Missing or disabled sensors show `N/A` instead of crashing Nova.

Special OLED screens are available for:

- Backup, including a simple downward arrow animation while saving.
- Backup Complete.
- Privacy Mode.
- Sleep Mode.
- Lockdown Mode.

Optional BH1750 light sensor settings:

```env
NOVA_LIGHT_ENABLED=false
NOVA_GPIO_BH1750_I2C_ADDRESS=35
```

`35` is decimal for the common `0x23` BH1750 address.

Optional voltage sensor support is reserved for the future:

```env
NOVA_VOLTAGE_ENABLED=false
```

## Hardware And Status Modules

Nova keeps hardware and status features in separate modules so missing parts do not crash the assistant.

- `nova/sensor_manager.py` gathers climate, Wi-Fi, voltage, and light readings for OLED and status reports.
- `nova/hardware.py` reports whether optional hardware systems are enabled or disabled.
- `nova/wifi_status.py`, `nova/light_sensor.py`, and `nova/voltage_sensor.py` safely detect individual hardware capabilities.
- `nova/lockdown.py`, `nova/sleep.py`, and `nova/privacy.py` manage operating modes.
- `nova/notifications.py` stores notification history.
- `nova/system_status.py` aggregates Nova's overall status.

Commands include:

```text
hardware status
sensor status
system status
oled status
volume status
set volume to 50
volume up
volume down
mute
unmute
show notifications
clear notifications
test oled
test backup screen
test sleep mode
test privacy mode
test lockdown mode
test notifications
test camera
test motion sensor
test ultrasonic sensor
test climate
test light sensor
test voltage sensor
test volume
test volume mute
test volume button
test router
test router status
inspect router
test microphone
test microphones
test voice
test wake word
test listen once
test accounts
test voice login
```

## TP-Link Router Control

Nova can control an authorized local TP-Link router through its local administration webpage using Playwright browser automation. This is designed for the owner-controlled local router only.

Required packages on the Raspberry Pi:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Private configuration belongs only in `.env.local`:

```env
# 📶 TP-Link Router Control
NOVA_ROUTER_CONTROL_ENABLED=true
NOVA_ROUTER_AUTOMATION_ENGINE=playwright
NOVA_ROUTER_URL=http://192.168.0.1/webpages/index.html
NOVA_ROUTER_MODEL=TP-Link Archer AX10000
NOVA_ROUTER_LOCAL_PASSWORD=your_local_router_password_here
NOVA_ROUTER_REQUIRE_ETHERNET=true
NOVA_ROUTER_REQUIRE_OFF_CONFIRMATION=true
NOVA_ROUTER_HEADLESS=true
NOVA_ROUTER_TIMEOUT_SECONDS=45
NOVA_ROUTER_DEBUG_SCREENSHOTS=false
```

Do not put the router password in Python files, README files, screenshots, or logs. `.env.local` is ignored by Git.

Router commands include:

```text
check the Wi-Fi status
which wireless bands are on
turn off the Wi-Fi
confirm Wi-Fi off
turn on the Wi-Fi
restore Wi-Fi
turn on guest network one
disable the 2.4 gigahertz guest network
turn on guest network two
enable 5G-1 guest Wi-Fi
turn on guest network three
disable the 5 gigahertz dash two guest network
is Smart Connect on
is OFDMA enabled
do a speed test
check our internet speed
what is our download speed
inspect router
```

Guest-network mapping:

| Nova name | Router control |
| --- | --- |
| Guest network 1 | 2.4 GHz guest network |
| Guest network 2 | 5 GHz-1 guest network |
| Guest network 3 | 5 GHz-2 guest network |

Main Wi-Fi radios remain separate from guest networks. If a guest network is enabled while its matching main radio is off, Nova turns on the matching main radio first and verifies both states.

For “turn off Wi-Fi,” Nova requires Ethernet by default and asks for a confirmation phrase before changing router settings. This protects Nova from cutting off its own wireless connection.

State and diagnostics:

- `data/router_state.json` stores only verified radio states, previous main Wi-Fi state, and latest speed-test results.
- `data/router_diagnostics.json` stores safe operation logs.
- Router passwords, cookies, tokens, and page HTML are never stored.
- Optional screenshots must be explicitly enabled and are Git-ignored.

Troubleshooting:

- If Nova says Playwright is unavailable, run `pip install -r requirements.txt` and `python -m playwright install chromium`.
- If Nova cannot reach the router, confirm the Pi is on the router LAN and the configured URL opens locally.
- If Nova says the Wireless page changed, run `inspect router` from the Pi and update selectors after reviewing the live page.
- Use `test router status` for a safe read-only check before trying commands that change Wi-Fi.

## Volume Control

Nova has a modular volume manager in `nova/volume.py`. It stores a software volume level in `data/settings.json` and can be expanded for a physical rotary encoder.

Configuration:

```env
NOVA_VOLUME_ENABLED=true
NOVA_VOLUME_HARDWARE_ENABLED=false
NOVA_VOLUME_DEFAULT=60
NOVA_VOLUME_MIN=0
NOVA_VOLUME_MAX=100
NOVA_GPIO_ROTARY_CLK_PIN=D5
NOVA_GPIO_ROTARY_DT_PIN=D6
NOVA_GPIO_ROTARY_SW_PIN=
NOVA_ROTARY_MUTE_ENABLED=true
```

If the dial hardware or GPIO packages are missing, Nova reports `Not Installed` and continues normally. The OLED dashboard shows a pixel speaker and volume bar. Pressing the rotary encoder button can toggle mute when `NOVA_GPIO_ROTARY_SW_PIN` is configured. While muted, the speaker gets an X but the volume bar keeps showing the saved level.

## Central Hardware GPIO Configuration

All GPIO assignments should live in the `.env.local` section named:

```text
# 🍓 Hardware GPIO Pin Assignments
```

Nova's configuration system prefers the centralized `NOVA_GPIO_*` values and keeps older feature-specific names only as backward-compatible fallbacks.

Examples:

```env
NOVA_GPIO_LED_RING_PIN=18
NOVA_GPIO_ROTARY_CLK_PIN=D5
NOVA_GPIO_ROTARY_DT_PIN=D6
NOVA_GPIO_ROTARY_SW_PIN=
NOVA_GPIO_DHT22_PIN=D17
NOVA_GPIO_PIR_PIN=D23
NOVA_GPIO_ULTRASONIC_TRIGGER_PIN=D24
NOVA_GPIO_ULTRASONIC_ECHO_PIN=D25
```

## Accounts And Voice Profiles

Nova supports basic local accounts with separate preferences, account-aware notes, per-user joke history, and a future-ready voice profile metadata field.

Account commands include:

```text
create account Caleb
make account Alex
switch account Caleb
who am I
current account
list accounts
```

## Offline Voice Commands

Nova supports offline voice commands through a USB microphone and Vosk. Typed commands remain available and are still the safest fallback.

Install the Python packages:

```bash
pip install -r requirements.txt
```

Install a Vosk English model locally. For example, download `vosk-model-small-en-us-0.15` from the official Vosk model list and place it at:

```text
models/vosk-model-small-en-us-0.15
```

Configuration:

```env
NOVA_MICROPHONE_ENABLED=true
NOVA_VOICE_COMMANDS_ENABLED=true
NOVA_VOICE_WAKE_WORD_ENABLED=false
NOVA_VOICE_WAKE_WORDS=hey nova,nova
NOVA_VOICE_TRANSCRIPTION_ENGINE=vosk
NOVA_VOSK_MODEL_PATH=models/vosk-model-small-en-us-0.15
NOVA_VOSK_MODEL_AUTO_DOWNLOAD=false
NOVA_VOSK_MODEL_URL=https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
NOVA_AUDIO_INPUT_DEVICE=
NOVA_VOICE_SAMPLE_RATE=16000
NOVA_VOICE_RECORD_SECONDS=5
NOVA_VOICE_COMMAND_TIMEOUT_SECONDS=8
NOVA_VOICE_SILENCE_SECONDS=1.2
NOVA_VOICE_WAKE_COOLDOWN_SECONDS=2
```

`NOVA_VOICE_SAMPLE_RATE=16000` is Nova's preferred Vosk rate. Some USB microphones reject 16 kHz through PortAudio/ALSA. In that case Nova now falls back to a supported microphone rate such as 44.1 kHz or 48 kHz and passes that same rate to Vosk.

Useful tests:

```text
test microphones
test microphone
test voice
test listen once
test wake word
test vosk model
```

If `NOVA_VOSK_MODEL_AUTO_DOWNLOAD=true`, Nova can download the configured model ZIP on first voice use or when you type:

```text
download vosk model
```

The default URL uses the official Alpha Cephei/Vosk model host. Some Vosk models also have Hugging Face mirrors, but Nova defaults to the official source.

Run one command from the shell:

```bash
python main.py --listen-once
```

Run continuous voice mode:

```bash
python main.py --voice
```

If `NOVA_VOICE_WAKE_WORD_ENABLED=true`, Nova continuously listens offline for `hey nova` or `nova`, then captures the following command. If wake-word mode is disabled, `--voice` repeatedly listens for short commands.

Privacy behavior:

- Voice recognition is offline-only.
- Nova streams microphone audio to Vosk in memory.
- Nova does not save microphone recordings by default.
- Cloud transcription is not used.

Voice login is fallback-ready but not full acoustic identity recognition yet. When enabled in the future, profiles should stay local on the Raspberry Pi unless explicitly changed later.

```env
NOVA_ACCOUNTS_ENABLED=true
NOVA_MICROPHONE_ENABLED=true
NOVA_VOICE_COMMANDS_ENABLED=true
NOVA_VOICE_WAKE_WORD_ENABLED=false
NOVA_VOICE_LOGIN_ENABLED=false
NOVA_VOICE_PROFILE_DIR=data/voice_profiles
NOVA_VOICE_CONFIDENCE_THRESHOLD=0.82
```

If the microphone or voice-recognition packages are missing, typed account switching still works.

## Backup Manager

Nova creates ZIP backups of local data, including notes, joke history, account files, settings, timers, alarms, and future JSON data files stored in `data/`.

Default settings:

```env
NOVA_BACKUP_ENABLED=true
NOVA_BACKUP_TIME=00:00
NOVA_BACKUP_KEEP_DAYS=30
```

Backups are stored in `backups/` with readable names such as:

```text
backup_2026-06-17_12-00_AM.zip
```

Nova starts a daily backup scheduler when the typed app starts. Manual commands include:

```text
backup now
create backup
make a backup
show backups
list backup history
backup status
restore latest backup
set backup time to 12:00 AM
change backup cleanup days to 30
clean backups
```

Restore is intentionally cautious. Nova validates the ZIP file and creates a safety backup before restoring files into `data/`.

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
- If WS2812B setup reports `Failed to create mailbox device`, run `sudo .venv/bin/python main.py` from the project folder.
- Offline microphone and wake-word support use Vosk when enabled. Typed commands remain the fallback.





My Email For Questions: plancd.nova@gmail.com
