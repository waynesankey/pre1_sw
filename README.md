# Release Notes
## Project: Preamp Controller 1
Wayne Sankey, Plano TX USA

Circa 2021/22.  Restarted 2026.

A microcontroller for a tube preamplifier.  The preamp has a custom PCB that fits vertically along the rear of the chassis and contains the audio connectors, relays for muting, audio input selection and power sequencing; and high end Muses 72320 volume control chips. The controller also drives a front panel 4x20 character backlit LCD display and accepts inputs from the front panel encoders and switches.
### Pre-release
There was an STM32 test board with C program used for a first controller project iteration but this was abandoned because PCBs were no longer available due to supply chain issues during the Covid pandemic.  Lead times became unknown, and I'm not prepared to wait some unbounded time, with the risk that boards would never again become available.

Therefore, the decision was made to upgrade to Raspberry Pi Pico using MicroPython for programming.  OOP in Python is much easier to write than C for STM32 and provides more stability, less complexity, less bugs, much easier and faster to write.  Also the far expanded and richer I/O capability of the Pico boards made an excellent update; in contrast the STM32 took a lot of time and careful planning to get the I/O to work in the project due to limited and specialized I/O.  The Pico was easy to configure and there are lots of GPIO leftover for later expansion if needed.

### Release 1.1.1
Feb 27, 2022: Initial Release to Github and onto amplifier target prototype.
Issue #1: upon release of standby, main screen items come back delayed in time.

### Release 1.2.1
Date:
Fixed Issue #1.  (not complete)

Added standby screen same as the STM32 program - different from the operational screen.

### Update to 2026 Micropython
Date: Jan 19 2026
Created git branch update_micropyton_v1_27_0 and uploaded that version uf2 to the testbed pico.  Device ran but there are no peripherals plugged in so it stopped running when it wanted some input from eg the display to set the brihtness.
When I want to continue, I'll need to get the full proto running.

To Do:
* break project into modules for modularity
* Add Tube Timer
* Add balance control
* testing 123