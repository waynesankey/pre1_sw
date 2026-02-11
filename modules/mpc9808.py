from config import *
from modules.tempsensor import TempSensor


class MPC9808(TempSensor):
    def __init__(self, i2c_bus, dis_obj):
        super().__init__()
        self.i2c = i2c_bus
        self.dis = dis_obj
        self.temp = 0x0000
        self.temperature = 0
        self.update()

    def update(self):
        self.read()
        self.calculate()
        self.dis.display_temp(self.temperature)

    def read(self):
        self.i2c.writeto(MPC9808_ADDR, bytearray([TEMP_DATA_REG]))
        readbuf = self.i2c.readfrom(MPC9808_ADDR, 2)
        self.temp = (readbuf[0] << 8) + readbuf[1]

    def calculate(self):
        self.temperature = self.temp
        if (self.temperature & 0x1000) == 0x1000:
            self.temperature = self.temperature & 0x0FFF
            self.temperature = self.temperature >> 4
            self.temperature = 256 - self.temperature
        else:
            self.temperature = self.temperature & 0x0FFF
            self.temperature = self.temperature >> 4
