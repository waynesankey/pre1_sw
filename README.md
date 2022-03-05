# Release Notes
## Project: Preamp Controller 1

### Pre-release
There was an STM32 test board with C program used for first project iteration but this was abandoned because PCBs were no longer freely available due to supply chain issues during Covid pandemic.  Lead times went to unknown times, and not prepared to wait some unbounded time, with the risk that boards would never again become available.

So, decision to upgrade to Raspberry Pi Pico using Python for programming.  OOP in Python much easier to write than C for STM32.  Also far expanded and richer I/O capability of Pico made a good update.

### Release 1.1.1
Initial Release to Github and onto amplifier target Feb 27, 2022.
Issue #1: upon release of standby, main screen items come back delayed in time.

### Release 1.2.1
Date:
Fixed Issue #1.
To Do:
Add Tube Timer