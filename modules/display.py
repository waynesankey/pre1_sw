import json
import time

from config import *


class Display:
    def __init__(self, i2c_bus):
        self.i2c = i2c_bus
        self.brightness = INITIAL_BRIGHTNESS
        self.change_brightness(0)
        self.clear_display()

        default_selections = '{"1": "Input 1", "2": "Input 2", "3": "Input 3", "4": "Input 4", "5": "Input 5"}'
        try:
            with open("selector.json", "r") as f:
                self.selector_info = json.load(f)
        except (ValueError, OSError):
            self.selector_info = json.loads(default_selections)
            print("Error: Could not load selector.json, using default selection strings")

    def clear_display(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_CLEAR]))
        time.sleep_us(1500)

    def set_brightness_standby(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_BRIGHTNESS, STANDBY_BRIGHTNESS]))
        time.sleep_us(100)

    def change_brightness(self, change):
        if change < -1 or change > 1:
            print("Error: change_brightness can only change by -1, 0, 1 - input change was", change)
            return
        self.brightness = max(0, min(self.brightness + change, MAX_BRIGHTNESS))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_BRIGHTNESS, self.brightness]))
        time.sleep_us(100)

    def set_brightness(self, brightness):
        self.brightness = max(0, min(brightness, MAX_BRIGHTNESS))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_BRIGHTNESS, self.brightness]))
        time.sleep_us(100)

    def get_brightness(self):
        return self.brightness

    def display_brightness(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"      Display       "))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(f"   Brightness: {self.brightness}".encode("utf-8")))

    def display_volume(self, volume_left, volume_right):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("{:<2}     Volume     {:>2}".format(volume_left, volume_right).encode("utf-8")))

    def display_balance(self, balance_left, balance_right):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("{:<2}     Balance    {:>2}".format(balance_left, balance_right).encode("utf-8")))

    def mute_on(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4 + MUTE_POSITION]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"Mute"))

    def mute_off(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4 + MUTE_POSITION]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"    "))

    def operate_on(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"Operate"))

    def operate_off(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"Standby"))

    def display_select(self, input_select):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"                    "))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        try:
            self.i2c.writeto(DISPLAY_ADDR, bytearray(self.selector_info[str(input_select)].encode("utf-8")))
        except KeyError:
            self.i2c.writeto(DISPLAY_ADDR, bytearray(b"Unknown Input       "))

    def display_splash(self):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"  4P1L Tube Preamp"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"Gingernut Labs 2022"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"MicroPython v1.19.1"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(("  SW Version " + SW_VERSION).encode("utf-8")))

    def filament_screen(self, count):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"     Preheating"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"   Tube Filaments"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"    Please Wait"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("    {:>2} seconds".format(count).encode("utf-8")))

    def bplus_screen(self, count):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"     Stabilizing"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"   B+ Power Supply"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"    Please Wait"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("    {:>2} seconds".format(count).encode("utf-8")))

    def standby_screen(self):
        self.clear_display()
        self.set_brightness_standby()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, STANDBY_POSITION]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"STANDBY"))

    def display_temp(self, temperature):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        degree_sign = 0xDF
        capital_c = 0x43
        buf = bytearray(("Temp " + str(temperature) + " ").encode("utf-8"))
        buf.append(degree_sign)
        buf.append(capital_c)
        self.i2c.writeto(DISPLAY_ADDR, buf)

    def display_tube_timer(self, tube_number, tube_active, tube_age_min, tube_age_hour):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"     Tube Timer"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(b"#  Act     Hr    Min"))

        active = "Y" if tube_active == "yes" else "N"
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        line = str(tube_number) + "   " + active + "   " + "{:>6}".format(tube_age_hour) + "    " + "{:>2}".format(tube_age_min)
        self.i2c.writeto(DISPLAY_ADDR, bytearray(line.encode("utf-8")))
