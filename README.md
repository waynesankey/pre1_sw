# Preamp Controller 1 (4P1L Tube Preamp)
Wayne Sankey, Plano TX USA

MicroPython firmware for a Raspberry Pi Pico based tube preamp controller.

The controller drives:
- 4x20 Newhaven LCD over I2C
- Muses 72320 volume control chips over SPI
- Latching relay matrix for input select, mute, filament, and B+ power sequencing
- Front panel encoders and switches
- Tube timer data in `tubeData.csv`

## Current Software Version
- `1.2.5`

## Project Structure
```text
pre1_sw/
├── main.py
├── config.py
├── modules/
│   ├── __init__.py
│   ├── display.py
│   ├── encoder.py
│   ├── muses72320.py
│   ├── mute.py
│   ├── operate.py
│   ├── relay.py
│   ├── selector.py
│   ├── state.py
│   ├── temperature.py
│   ├── tube_timer.py
│   └── volume.py
├── lib/
│   └── queue.py
├── selector.json
├── tubeData.csv
└── README.md
```

## Refactor Summary (v1.2.5)
- Moved constants/configuration into `config.py`
- Split monolithic `main.py` class definitions into one-class-per-file modules
- Separated `Mute` functionality into `modules/mute.py` (no longer part of display logic)
- Kept async message-queue architecture in `main.py`
- Preserved full tube preamp state model and sequencing behavior

## State Machine (Not Simplified)
This project keeps the full tube-oriented state flow:
- `STATE_STARTUP`
- `STATE_FILAMENT`
- `STATE_BPLUS`
- `STATE_OPERATE`
- `STATE_STANDBY`
- `STATE_BALANCE`
- `STATE_TT_DISPLAY`
- `STATE_BRIGHTNESS`

Tube timer and temperature updates remain active in the same operational contexts as before.

## Module Responsibilities
- `modules/state.py`: main state transitions and dispatch logic
- `modules/display.py`: LCD UI rendering, splash, standby, warmup, tube timer screens
- `modules/mute.py`: mute switch/state behavior, soft mute ramps, forced mute paths
- `modules/relay.py`: relay shift-register writes, input select, filament/B+/mute relay control
- `modules/muses72320.py`: volume chip writes and soft ramp methods
- `modules/volume.py`: volume/balance math and display/chip updates
- `modules/selector.py`: input selection behavior with soft volume down/up around switching
- `modules/temperature.py`: MPC9808 read/calculate/display
- `modules/tube_timer.py`: tube age read/increment/write and display selection
- `modules/encoder.py`: quadrature encoder decode helper
- `modules/operate.py`: OPERATE switch state helper

## Release Notes
- `1.2.5` (2026-02-10): modularized codebase, extracted `config.py`, split `Mute` class, retained full tube-state sequencing.
