# Nova Master Architecture

Nova is a Raspberry Pi based smart assistant designed by Caleb. It should become a private, expandable, family-friendly assistant that combines hardware and software into one repairable device.

Nova should be helpful, private, reliable, expandable, and friendly. Every feature should move Nova closer to those goals.

## Core Goals

- Work online.
- Work offline.
- Continue functioning if some hardware is disconnected.
- Support future upgrades.
- Be easy to repair.
- Be easy to understand.

Nova should never completely fail because one sensor, device, or API is missing. If there is no microphone, use typed commands. If there are no speakers, use text output. If there is no internet, use offline systems.

## Current Hardware

- Raspberry Pi
- Yellow/blue OLED display
- 12 LED ring
- LED diffuser
- Camera module
- PIR motion sensor
- Ultrasonic sensor
- DHT22 temperature/humidity sensor
- BH1750 light sensor
- Voltage sensor
- Two speakers
- Mini breadboard
- Jumper wires

Future hardware should be easy to add.

## OLED System

The OLED display shows Nova's status and useful device information.

Current target display:

- UCTRONICS 0.96 inch 128x64 yellow/blue OLED.
- SSD1306 driver.
- I2C interface.
- Raspberry Pi I2C bus 1.
- VCC to physical pin 1, 3.3V.
- GND to physical pin 6, ground.
- SDA to physical pin 3, GPIO2/SDA1.
- SCL to physical pin 5, GPIO3/SCL1.

Planned information:

- Face
- Time
- Temperature
- Light level
- Wi-Fi status
- Voltage
- Backup status
- Lockdown status

Planned states:

- Ready
- Listening
- Thinking
- Speaking
- Backing up
- Privacy mode
- Lockdown mode
- Sleeping

The OLED system should be expandable.

Current dashboard layout:

- Top: small pixel Nova face, time, and Wi-Fi signal bars.
- Middle: temperature and humidity.
- Lower: Wi-Fi text, voltage, and light level.
- Bottom: current Nova mode.

Special screens:

- Backup animation and Backup Complete.
- Lockdown warning screen.
- Privacy lock screen.
- Sleep face with Zzz.

Missing sensors must display `N/A` and must not crash Nova.

Supporting modules:

- `nova/oled.py`: display rendering and refresh loop.
- `nova/oled_status.py`: lightweight OLED status summary.
- `nova/sensor_manager.py`: combined sensor snapshot for OLED and commands.
- `nova/wifi_status.py`: Wi-Fi detection.
- `nova/light_sensor.py`: BH1750 detection.
- `nova/voltage_sensor.py`: voltage sensor placeholder and future ADC integration point.
- `nova/hardware.py`: enabled/disabled hardware summary.
- `nova/system_status.py`: aggregate status for app commands.
- `nova/notifications.py`: notification history.
- `nova/lockdown.py`, `nova/sleep.py`, and `nova/privacy.py`: operating mode managers.
- `nova/camera.py`, `nova/motion.py`, and `nova/ultrasonic.py`: safe hooks for security hardware.
- `nova/diagnostics.py`: terminal test commands for major systems.
- `nova/volume.py`: shared software volume state and future rotary encoder integration.

## Volume Control System

Nova stores volume locally in `data/settings.json` and exposes it through `nova.volume.get_volume_manager()`.

Current behavior:

- Software volume is always available when enabled.
- Physical dial support is optional and reports `Not Installed`, `Missing`, or `Configured`.
- OLED draws a small pixel speaker and horizontal volume bar.
- Rotary encoder SW can toggle mute when configured.
- Muted volume shows an X indicator while keeping the saved volume bar visible.
- Future expansion can add separate speech, notification, alarm, and music volumes.

## Account And Voice Profile System

Accounts are stored locally in `data/users.json`.

Current account data:

- Name.
- Preferences.
- Account-aware notes.
- Per-user joke history.
- Voice profile metadata.

Voice commands are available as an optional local-only Raspberry Pi feature through Vosk. The voice path streams USB microphone audio to an offline recognizer in memory, then routes recognized text through the same Nova command router used by typed mode. Vosk wake-word mode can continuously listen for configured phrases such as "hey nova" before capturing a command. If the microphone, Vosk package, or model files are unavailable, Nova reports the problem and typed commands continue to work.

Voice login remains fallback-ready and stores only compact local metadata when explicitly enabled. It does not upload voice samples. Acoustic identity recognition is not implemented yet.

Modules:

- `nova/microphone.py`: USB microphone detection, device listing, and streaming.
- `nova/speech_to_text.py`: offline Vosk transcription.
- `nova/wake_word.py`: Vosk-based wake-word detection.
- `nova/voice_loop.py`: command capture loop and integration with Nova's status displays.

## Temperature And Humidity Sensor

Current target sensor:

- DHT22/AM2302 temperature and humidity sensor.
- VCC to physical pin 1, 3.3V.
- DATA/OUT to physical pin 11, GPIO17.
- GND to physical pin 9, ground.
- Bare 4-pin sensors need a 10k pull-up resistor between VCC and DATA.

The climate module should never crash Nova if the sensor is missing or a reading fails. The OLED should show placeholder temperature and humidity values until valid readings are available.

## LED Ring System

The LED ring lets people understand Nova's status from across the room.

Status colors:

- Green: ready
- Blue: listening
- Rainbow: thinking
- Purple: speaking
- White: backup
- Orange: privacy
- Red: lockdown

Animations should remain simple. The LED ring should always agree with the OLED status.

## JokeStack System

The joke system lets Nova tell jokes.

Requirements:

- Large joke collection.
- Avoid immediate repeats.
- Separate joke history for each user.
- Search online for new jokes when available.
- Continue working offline.
- Store joke history.
- Store joke usage counts.

If all jokes are used, Nova should fetch new jokes when online. Offline, Nova may reuse old jokes only when necessary.

Future expansion:

- Joke ratings.
- Favorite jokes.
- Most-used jokes.

## Dictionary System

The dictionary system explains words and concepts, including definitions, technology terms, science terms, and general knowledge. It should function offline whenever possible, with online lookup used to expand information when available.

## Math System

The math system solves problems, including addition, subtraction, multiplication, division, fractions, percentages, algebra, and word problems. Online and offline solving should both exist.

## Notes System

The notes system lets users save, search, and organize information such as shopping lists, study notes, ideas, and Nova development notes. Notes must be included in backups.

## Account System

Each user should eventually have a name, birthday, joke history, preferences, and personal notes. Users should not interfere with each other.

## Weather System

The weather system provides temperature, conditions, forecast, and location-based weather. Weather requires internet and must gracefully fail when offline.

## Backup System

Backups protect Nova's data.

Schedule:

- Daily at midnight.
- Configurable with `NOVA_BACKUP_TIME`.
- Old backups are cleaned after a configurable number of days.

Included data:

- Notes
- Joke history
- Accounts
- Settings
- Data files

Current implementation:

- `nova/backups.py` owns backup creation, history, cleanup, settings, and restore.
- Backups are ZIP files stored in `backups/`.
- Restore validates archive paths and creates a safety backup before writing restored files.
- The app scheduler runs daily backups while Nova is running.
- OLED and LED can show `backup` status during manual, scheduled, and restore actions.

Example backup name:

```text
backup_2026-06-17_12-00_AM.zip
```

Backups should be restorable.

## Lockdown Mode

Lockdown mode is Nova's security mode.

Possible hardware:

- Camera
- PIR
- Ultrasonic sensor
- Speakers
- OLED
- LED ring

Potential actions:

- Alert user.
- Observe room.
- Play warning.
- Flash red.

OLED text:

```text
LOCKDOWN MODE
```

Example speaker line:

```text
Please leave now, you sneaky pirates.
```

## Privacy Mode

Privacy mode temporarily reduces activity, limits responses, uses an orange LED, and displays Privacy Mode on the OLED.

## Sleep Mode

Sleep mode reduces activity with a sleeping OLED screen, lower brightness, and quiet operation.

## Online Mode

Available features:

- Weather
- Online jokes
- Web search
- Expanded knowledge

## Offline Mode

Available features:

- Local jokes
- Notes
- Dictionary
- Math
- Settings

Unavailable features:

- Weather
- Live web search

## File Architecture Rules

Every feature should have a clear file location, be modular, and support future expansion. Avoid giant files when possible. Keep major systems separated, including OLED, LED, jokes, backups, and lockdown.

## Hardware GPIO Configuration

GPIO assignments live in one `.env` section:

```text
# 🍓 Hardware GPIO Pin Assignments
```

Use centralized `NOVA_GPIO_*` settings for hardware pins. Feature-specific pin settings should only exist as backward-compatible fallbacks. New hardware modules should add their pin names to the centralized section instead of creating a separate pin setting elsewhere.

Current centralized assignments include OLED I2C, LED ring, rotary encoder CLK/DT/SW, DHT22, PIR, ultrasonic trigger/echo, BH1750 I2C, camera connector, future buttons, future buzzer, future relays, and future sensors.

## Router Control System

Router control is a local-only owner-authorized feature for the TP-Link Archer AX10000. The router does not provide an API key, so Nova uses Playwright browser automation against the local router admin page.

Modules:

- `nova/router_commands.py`: recognizes router, Wi-Fi, guest-network, and speed-test phrases.
- `nova/router_control.py`: owns Playwright login, navigation, toggle reads, toggle changes, verification, speed tests, and safe diagnostics.
- `nova/router_status.py`: owns radio-state names, guest-to-main mapping, saved previous state, and latest speed-test result.

Security boundaries:

- Router password is read only from `.env.local`.
- Passwords, cookies, session tokens, full page HTML, and screenshots are not logged.
- `.env.local` and optional router screenshot folders are Git-ignored.
- Router-changing commands require an authenticated Nova App session when sent through the PWA command endpoint.
- Turning off all Wi-Fi requires confirmation and prefers Ethernet.

State flow:

```text
User command
  -> nova/router_commands.py
  -> nova/router_control.py
  -> TP-Link local admin page
  -> verified router state
  -> data/router_state.json
  -> response/status/notifications
```

Main radios are tracked separately:

- 2.4 GHz
- 5 GHz-1
- 5 GHz-2

Guest networks are tracked separately:

- Guest network 1: 2.4 GHz guest network
- Guest network 2: 5 GHz-1 guest network
- Guest network 3: 5 GHz-2 guest network

Smart Connect and OFDMA are separate features and must not be treated as Wi-Fi availability by themselves.

The first implementation uses the labels provided by the owner and includes an `inspect router` command for safe live page discovery. If TP-Link changes the page structure, Nova must fail gracefully and report that selectors need to be inspected again.

## Data Flow Rules

```text
User Input
  -> Nova Core
  -> Feature Module
  -> Data Storage
  -> Response
```

Major systems should follow predictable data flow.

## Development Rules

Before coding a feature, explain:

1. The feature.
2. Affected files.
3. New files.
4. Data flow.
5. Future expansion.
6. Risks.

Then generate code.

## Testing Rules

Every feature should include:

- Test plan.
- Failure cases.
- Recovery plan.
- Offline testing.
- Online testing.

## Future Roadmap

Potential future systems:

- Phone notifications
- Home automation
- Computer vision
- Better AI memory
- Advanced weather
- Battery monitoring
- Music control
- Remote dashboard

Additional features should follow the same design philosophy as existing systems.
