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
        self.i2c.writeto(DISPLAY_ADDR, bytearray("      Display       "))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray(f"   Brightness: {self.brightness}"))

    def display_volume(self, volume_left, volume_right):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("{:<2}     Volume     {:>2}".format(volume_left, volume_right)))

    def display_balance(self, balance_left, balance_right):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("{:<2}     Balance    {:>2}".format(balance_left, balance_right)))

    def mute_on(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4 + MUTE_POSITION]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("Mute"))

    def mute_off(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4 + MUTE_POSITION]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("    "))

    def operate_on(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("Operate"))

    def operate_off(self):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("Standby"))

    def display_select(self, input_select):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("                    "))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        try:
            self.i2c.writeto(DISPLAY_ADDR, bytearray(self.selector_info[str(input_select)]))
        except KeyError:
            self.i2c.writeto(DISPLAY_ADDR, bytearray("Unknown Input       "))

    def display_splash(self):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("  4P1L Tube Preamp"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("Gingernut Labs 2022"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("MicroPython v1.19.1"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("  SW Version " + SW_VERSION))

    def filament_screen(self, count):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("     Preheating"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("   Tube Filaments"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("    Please Wait"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("    {:>2} seconds".format(count)))

    def bplus_screen(self, count):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("     Stabilizing"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("   B+ Power Supply"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("    Please Wait"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("    {:>2} seconds".format(count)))

    def standby_screen(self):
        self.clear_display()
        self.set_brightness_standby()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, STANDBY_POSITION]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("STANDBY"))

    def display_temp(self, temperature):
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        degree_sign = 0xDF
        capital_c = 0x43
        buf = bytearray("Temp " + str(temperature) + " ")
        buf.append(degree_sign)
        buf.append(capital_c)
        self.i2c.writeto(DISPLAY_ADDR, buf)

    def display_tube_timer(self, tube_number, tube_active, tube_age_min, tube_age_hour):
        self.clear_display()
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("     Tube Timer"))
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3]))
        self.i2c.writeto(DISPLAY_ADDR, bytearray("#  Act     Hr    Min"))

        active = "Y" if tube_active == "yes" else "N"
        self.i2c.writeto(DISPLAY_ADDR, bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4]))
        line = str(tube_number) + "   " + active + "   " + "{:>6}".format(tube_age_hour) + "    " + "{:>2}".format(tube_age_min)
        self.i2c.writeto(DISPLAY_ADDR, bytearray(line))
