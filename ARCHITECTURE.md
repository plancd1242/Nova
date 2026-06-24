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

Included data:

- Notes
- Joke history
- Accounts
- Settings
- Data files

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
