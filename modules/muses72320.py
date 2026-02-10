import time

from config import *


class Muses72320:
    def __init__(self, spi_bus, cs_pin):
        self.spi = spi_bus
        self.cs = cs_pin
        self.vol_left = 0
        self.vol_right = 0
        self.write(self.vol_left, self.vol_right)

    def write(self, left, right):
        data_left = MUSES_ATTEN_0 + 2 * (MAX_VOLUME - left)
        if left == 0:
            data_left = 0xFF
        print("Volume chip data left channel is", data_left)

        data_right = MUSES_ATTEN_0 + 2 * (MAX_VOLUME - right)
        if right == 0:
            data_right = 0xFF

        for buf in (
            bytearray([data_left, LEFT_LSB_0]),
            bytearray([data_left, LEFT_LSB_1]),
            bytearray([data_right, RIGHT_LSB_0]),
            bytearray([data_right, RIGHT_LSB_1]),
        ):
            self.cs.value(0)
            self.spi.write(buf)
            self.cs.value(1)

    def vol_down_soft(self, left, right):
        largest = max(left, right)
        while largest > 0:
            if left > 0:
                left -= 1
            if right > 0:
                right -= 1
            self.write(left, right)
            largest -= 1
            time.sleep_ms(4)

    def vol_up_soft(self, left, right):
        largest = max(left, right)
        lvol = 0
        rvol = 0
        while largest > 0:
            if lvol < left:
                lvol += 1
            if rvol < right:
                rvol += 1
            self.write(lvol, rvol)
            largest -= 1
            time.sleep_ms(4)

    def vol_mute_immediate(self):
        self.write(0, 0)
