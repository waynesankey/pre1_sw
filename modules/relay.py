import time

from config import *


class Relay:
    def __init__(self, spi_bus, cs_pin):
        self.spi = spi_bus
        self.cs = cs_pin
        self.relay_array = [0 for _ in range(16)]

        # SPI quirk workaround + deterministic startup state.
        self.mute_on()
        self.mute_on()
        self.deselect_all()
        time.sleep_ms(100)
        self.mute_on()
        self.deselect_all()

    def write(self):
        relays0 = 0x00
        relays1 = 0x00
        for i in range(0, 8):
            relays0 = (relays0 << 1) | (0x01 if self.relay_array[i] else 0x00)
        for i in range(8, 16):
            relays1 = (relays1 << 1) | (0x01 if self.relay_array[i] else 0x00)
        print("relays0 and relays1 hex %x %x" % (relays0, relays1))
        self.cs.value(0)
        self.spi.write(bytearray([relays0, relays1]))
        self.cs.value(1)

    def filament_on(self):
        print("Turning on Filament Relay")
        self.relay_array[REL_FILAMENT] = REL_ON
        self.write()

    def filament_off(self):
        print("Turning off Filament Relay")
        self.relay_array[REL_FILAMENT] = REL_OFF
        self.write()

    def bplus_on(self):
        print("Turning on B+ Relay")
        self.relay_array[REL_BPLUS] = REL_ON
        self.write()

    def bplus_off(self):
        print("Turning off B+ Relay")
        self.relay_array[REL_BPLUS] = REL_OFF
        self.write()

    def mute_on(self):
        print("Turning on Mute Relay")
        self.relay_array[REL_MUTE] = REL_ON
        self.write()

    def mute_off(self):
        print("Turning off Mute Relay")
        self.relay_array[REL_MUTE] = REL_OFF
        self.write()

    def deselect_all(self):
        self.relay_array[REL_SEL1RESET] = REL_ON
        self.relay_array[REL_SEL2RESET] = REL_ON
        self.relay_array[REL_SEL3RESET] = REL_ON
        self.relay_array[REL_SEL4RESET] = REL_ON
        self.relay_array[REL_SEL5RESET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL1RESET] = REL_OFF
        self.relay_array[REL_SEL2RESET] = REL_OFF
        self.relay_array[REL_SEL3RESET] = REL_OFF
        self.relay_array[REL_SEL4RESET] = REL_OFF
        self.relay_array[REL_SEL5RESET] = REL_OFF
        self.write()

    def select(self, input_select):
        self.deselect_all()
        time.sleep_ms(REL_LATCH_TIME)
        if input_select == SELECT_STREAMING:
            self.select_streaming()
        elif input_select == SELECT_CD:
            self.select_cd()
        elif input_select == SELECT_PHONO:
            self.select_phono()
        elif input_select == SELECT_AUX1:
            self.select_aux1()
        elif input_select == SELECT_AUX2:
            self.select_aux2()

    def select_streaming(self):
        self.relay_array[REL_SEL1SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL1SET] = REL_OFF
        self.write()

    def select_cd(self):
        self.relay_array[REL_SEL2SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL2SET] = REL_OFF
        self.write()

    def select_phono(self):
        self.relay_array[REL_SEL3SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL3SET] = REL_OFF
        self.write()

    def select_aux1(self):
        self.relay_array[REL_SEL4SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL4SET] = REL_OFF
        self.write()

    def select_aux2(self):
        self.relay_array[REL_SEL5SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL5SET] = REL_OFF
        self.write()
