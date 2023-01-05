from machine import Pin, I2C
import os
import time
import uasyncio
import queue
import json



# have volume encoder class split out from volume class - need to do same thing for the sel encoder
# have message system set up with uasyncio library for pattern:
# detect input change (async polled) then send message to the active part of the program
# remove the 1s timer because there's an asyncio 1s beat ???
# remove the 10ms timer because its not needed to debounce the nutton pushes any more
# continue with the State class and methods to run the amp
# add more functions such as balance



###################################################################
# SW Version
SW_VERSION = "1.2.3"

#minor version 2 adds tube timer

###################################################################
# Display Constants - Newhaven Display NHD-0420D3Z-NSW-BBW-V3

# I2C Address
DISPLAY_ADDR = 0x28

# Registers
REG_PREFIX = 0xFE
REG_POSITION = 0x45
REG_CLEAR = 0x51
REG_CONTRAST = 0x52
REG_BRIGHTNESS = 0x53
INITIAL_BRIGHTNESS = 0x02
STANDBY_BRIGHTNESS = 0x02
MAX_BRIGHTNESS = 0x08

DISPLAY_LINE1 = 0x00
DISPLAY_LINE2 = 0x40
DISPLAY_LINE3 = 0x14
DISPLAY_LINE4 = 0x54

MUTE_POSITION = 16
STANDBY_POSITION = 0x47


# State constants
STATE_STARTUP = 0
STATE_FILAMENT = 1
STATE_BPLUS = 2
STATE_OPERATE = 3
STATE_STANDBY = 4
STATE_TUBETIMER = 5
STATE_BALANCE = 6
STATE_TT_DISPLAY = 7
STATE_BRIGHTNESS = 8



###################################################################
# MPC9808 Temperature Sensor Constants
MPC9808_ADDR = 0x18

TEMP_DATA_REG = 0x05


###################################################################
# Muses 72320 Volume Chip Constants
#Left volume chip is at address 0
#Right volume chip is at address 1
#Two balanced chips = one for left and one for right
#Write same attenuation data to left and right channels for each chip.
LEFT_LSB_0 = 0x00
LEFT_LSB_1 = 0x20
RIGHT_LSB_0 = 0x01
RIGHT_LSB_1 = 0x21

MUSES_ATTEN_0 = 0x10


###################################################################
# Relay Constants - Panasonic DS2E-SL2-DC12V
# These are really high quality latching relays used in super high end preamps eg Pass Labs.

# Relays are reversed bits (it's a SR so the first bit to arrive ends up at the end of the SR):
# Also, the reverse bit ordering in the SPI class is not implemented so you can't just code
# firstbit=machine.SPI.LSB to implement the bit reversing.
# 0: Filament
# 1: B+
# 2: Mute
# 3: Sel 1 Set
# 4: Se1 1 Reset
# 5: Sel 2 Set
# 6: Se1 2 Reset
# 7: Sel 3 Set
# 8: Se1 3 Reset
# 9: Sel 4 Set
# 10: Se1 4 Reset
# 11: Sel 5 Set
# 12: Se1 5 Reset

REL_ON = 1
REL_OFF = 0

REL_LATCH_TIME = 20   # this is about double the required amount

REL_FILAMENT = 0
REL_BPLUS = 1
REL_MUTE = 2
REL_SEL1SET = 3
REL_SEL1RESET = 4
REL_SEL2SET = 5
REL_SEL2RESET = 6 
REL_SEL3SET = 7
REL_SEL3RESET = 8
REL_SEL4SET = 9
REL_SEL4RESET = 10
REL_SEL5SET = 11
REL_SEL5RESET = 12


# States
RELAY_ST_STARTUP = 0        
RELAY_ST_DESELECT_ALL = 1   # energize all select reset coils, leave power as is


# Shift Register contents
RELAY_SR_STARTUP_ACTIVE = 0x1550     # energize select relay reset coils - OR mask
RELAY_SR_STARTUP_INACTIVE = 0x0007   # de-energize select relays - AND mask

RELAY_SR_FILAMENT_ON = 0x0001
RELAY_SR_BPLUS_ON = 0x0002
RELAY_SR_MUTE_ON = 0x0004


#timer
timer1s = 0


###################################################################
# Product Constants
MAX_VOLUME = 64
MAX_BALANCE = 6     # the volume is in 1 dB steps, so this is a +/- 12dB side-to-side difference 

MUTE_ON = 0          # grounded when switch in up position, two lugs go towards bottom of chassis
MUTE_OFF = 1

MUTE_ST_OFF = 0
MUTE_ST_ON = 1

OPERATE_ON = 0       # grounded when switch in up position, two lugs go towards bottom of chassis
OPERATE_OFF = 1

OPERATE_ST_OFF = 0   # standby
OPERATE_ST_ON = 1    # operate

PB_PUSHED = 0        # pushbutton depressed
PB_RELEASED = 1      # pushbutton released


SELECT_NONE = 0
SELECT_STREAMING = 1
SELECT_CD = 2
SELECT_PHONO = 3
SELECT_AUX1 = 4
SELECT_AUX2 = 5



# Messages to pass on the Queue
NULL_MESSAGE = 0

L_PB_PUSHED = 1
R_PB_PUSHED = 2
VOL_KNOB_CCW = 3
VOL_KNOB_CW = 4
SEL_KNOB_CCW = 5
SEL_KNOB_CW = 6
SW_MUTE_ON = 7
SW_MUTE_OFF = 8
SW_OPERATE_ON = 9
SW_OPERATE_OFF = 10
UPDATE_TEMP = 11
SECOND_BEAT = 12
MINUTE_BEAT = 13


SPLASH_DELAY = 3
FILAMENT_DELAY = 3  # change this to 45 when creating working loads
BPLUS_DELAY = 3



###################################################################
# Declare Pins

# Volume Encoder GP5 and GP6 with pullups
vol0_in = Pin(5, Pin.IN, Pin.PULL_UP)
vol1_in = Pin(6, Pin.IN, Pin.PULL_UP)

# Volume pushbutton ? GP7 with pullups
volpb_in = Pin(7, Pin.IN, Pin.PULL_UP)

# Select Encoder GP2 and GP3 with pullups
sel0_in = Pin(2, Pin.IN, Pin.PULL_UP)
sel1_in = Pin(3, Pin.IN, Pin.PULL_UP)

# Select pushbutton ? GP4 with pullups
selpb_in = Pin(4, Pin.IN, Pin.PULL_UP)

# Mute Switch with pullups
mute_in = Pin(9, Pin.IN, Pin.PULL_UP)

# Operate Switch with pullups
operate_in = Pin(8, Pin.IN, Pin.PULL_UP)

# Led to flash with other core
led_red = Pin(25, Pin.OUT)




###################################################################
# Functions



###################################################################
# Classes


class Vol_encoder():
    def __init__(self):
        self.current = vol1_in.value() << 1
        self.current = self.current + vol0_in.value()
        self.last = self.current
        #print("initializing vol_enc object, current encoder position is %x" % self.current)
        return
        
    def change(self):
        #print ("in vol change")
        volume_change = 0
        self.current = vol1_in.value() << 1
        self.current = self.current + vol0_in.value()
        if (self.current != self.last):
            #print("volume encoder changed, new value is", self.current, "old value was", self.last)
            if self.last == 3 and self.current == 1:
                volume_change = 1
            elif self.last == 3 and self.current == 2:
                volume_change = -1
            self.last = self.current
            #print("volume_change is ", volume_change)
        return volume_change
    
    def reset_position(self):
        """Used to reset the encoder position so no changes are pending.  Used in long delay debounce loop so when the debounce returns, the current encoder position is zeroed out."""
        self.current = vol1_in.value() << 1
        self.current = self.current + vol0_in.value()
        self.last = self.current
        return
        
    def print_current_position(self):
        position = 0
        position = vol1_in.value() << 1
        position = position + vol0_in.value()
        #print("vol encoder position is ", position)
        return
    
    
class Volume():
    """Class to handle the volume and balance methods and members.  Balance is handled as a left/right delta to the volume."""
    def __init__(self):
        self.volume = 0
        self.balance = 0
        self.volume_left = 0
        self.volume_right = 0
        self.balance_left = 0
        self.balance_right = 0
        return
    
    def update_volume(self, volume_change):
        """The volume number is changed by this method which will then take into account the balance and write the correct new volume L/R to the display and volume chips.
        This method is only called in the OPERATE state.
        """
        
        self.volume = self.volume + volume_change

        # limit volume to the allowed bounds and run through routine to clean up any problems (could return from here really but keep going)
        if (self.volume < 0):
            self.volume = 0
        if (self.volume > MAX_VOLUME):
            self.volume = MAX_VOLUME

        # now split the volume into left and right by applying balance
        self.volume_left = self.volume - self.balance;
        self.volume_right = self.volume + self.balance;

        # limit the post-balance L/R volumes
        if (self.volume_left < 0):
            self.volume_left  = 0
        if (self.volume_right < 0):
            self.volume_right = 0

        if (self.volume_left > MAX_VOLUME):
            self.volume_left = MAX_VOLUME
        if (self.volume_right > MAX_VOLUME):
            self.volume_right = MAX_VOLUME

        # now write L/R values to the display and volume chips
        #print("In update_volume, left volume is", self.volume_left, " and right volume is ", self.volume_right)
        dis.display_volume(self.volume_left, self.volume_right)
        mus.write(self.volume_left, self.volume_right)
        return

    def update_balance(self, balance_change):
        """This method is only called in the BALANCE state."""
        # update the balance
        self.balance = self.balance + balance_change
        
        # limit balance value
        if (self.balance < 0-MAX_BALANCE):
            self.balance = 0-MAX_BALANCE
        if (self.balance > MAX_BALANCE):
            self.balance = MAX_BALANCE
        
        # split the balance between left and right and calculate the L/R volumes
        self.balance_left = 0 - self.balance
        self.balance_right = self.balance
        self.volume_left = self.volume + self.balance_left
        self.volume_right = self.volume + self.balance_right
        
        # now write L/R values to the display and volume chips
        dis.display_balance(self.balance_left, self.balance_right)
        mus.write(self.volume_left, self.volume_right)
        return
    
    def get_current_volume_left(self):
        return self.volume_left
    
    def get_current_volume_right(self):
        return self.volume_right
    
    
    

class Sel_encoder():
    def __init__(self):
        self.select = SELECT_STREAMING
        self.current = sel1_in.value() << 1
        self.current = self.current + sel0_in.value()
        self.last = self.current
        print("initializing sel object, current encoder position is %x" % self.current)
        return
        
    def change(self):
        #print ("in sel change")
        select_change = 0
        self.current = sel1_in.value() << 1
        self.current = self.current + sel0_in.value()
        if (self.current != self.last):
            print("selector encoder changed, last value was", self.last, "and new value is", self.current)
            if self.last == 3 and self.current == 1:
                select_change = 1
            elif self.last == 3 and self.current == 2:
                select_change = -1
            self.last = self.current
            print("select_change is ", select_change)
        return select_change

    def reset_position(self):
        """Used to reset the encoder position so no changes are pending.  Used in long delay debounce loop so when the debounce returns, the current encoder position is zeroed out."""
        self.current = sel1_in.value() << 1
        self.current = self.current + sel0_in.value()
        self.last = self.current
        return

    def update_select(self, select_change):
        print("Entering update_select,current select is %i and change is %i" % (self.select, select_change))
        self.select = self.select + select_change
        if (self.select < SELECT_STREAMING):
            self.select = SELECT_STREAMING
            return
        if (self.select > SELECT_AUX2):
            self.select = SELECT_AUX2
            return
        print("In update_select, new select is", self.select)

        volume_left = vol.get_current_volume_left()
        volume_right = vol.get_current_volume_right()
        mus.vol_down_soft(volume_left, volume_right)
        dis.display_select(self.select)
        rel.select(self.select)
        mus.vol_up_soft(volume_left, volume_right)
        return    
    

    def select_immediate(self):
        """operate currently selected input with no delay for example at state changes"""
        dis.display_select(self.select)
        rel.select(self.select)
        return


    def get_current_select(self):
        return self.select
    
    def print_current_position(self):
        position = 0
        position = sel1_in.value() << 1
        position = position + sel0_in.value()
        print("sel encoder position is ", position)
        return



class Mute():
    def __init__(self):
        self.mute_switch = mute_in.value()
        self.mute_switch_last = self.mute_switch
        self.mute_state = MUTE_ST_OFF
        if (self.mute_switch == MUTE_ON):
            self.mute_state = MUTE_ST_ON
        return
    
    def change(self):
        self.mute_switch = mute_in.value()
        if ((self.mute_switch == MUTE_ON) and (self.mute_switch_last == MUTE_OFF)): #turn on event
            self.mute_switch_last = self.mute_switch
            self.mute_state = MUTE_ST_ON
            return 1
        elif((self.mute_switch == MUTE_OFF) and (self.mute_switch_last == MUTE_ON)): #turn off event
            self.mute_switch_last = self.mute_switch
            self.mute_state = MUTE_ST_OFF
            return 2
        else: # no change
            return 0     
    
    def update_mute(self):  #update display and relays
        print("update_mute: self.mute_state is ", self.mute_state)
        if(self.mute_state == MUTE_ST_ON):
            dis.mute_on()
            volume_left = vol.get_current_volume_left()
            volume_right = vol.get_current_volume_right()
            mus.vol_down_soft(volume_left, volume_right)
            rel.mute_on()
        else:
            rel.mute_off()
            volume_left = vol.get_current_volume_left()
            volume_right = vol.get_current_volume_right()
            mus.vol_up_soft(volume_left, volume_right)
            dis.mute_off()
        return
    
    # use this to detect current switch position and execute mute functions if the mute state does
    # not match the switch
    def execute_mute(self):
        self.mute_switch = mute_in.value()
        if ((self.mute_switch == MUTE_ON) and (self.mute_state == MUTE_ST_OFF)):
            self.mute_switch_last = self.mute_switch
            self.mute_state = MUTE_ST_ON
            self.update_mute()
        if((self.mute_switch == MUTE_OFF) and (self.mute_state == MUTE_ST_ON)):
            self.mute_switch_last = self.mute_switch
            self.mute_state = MUTE_ST_OFF
            self.update_mute()
        return
        

    def force_mute(self):
        """use this to mute the outputs without first getting switch setting - for example when going on standby"""
        self.mute_state = MUTE_ST_ON
        self.update_mute()
        return


    def mute_immediate(self):
        """instant set mute relay and display to switch positionif mute ON, soft mute release if OFF"""
        self.mute_switch = mute_in.value()
        self.mute_switch_last = self.mute_switch
        if(self.mute_switch == MUTE_ON):
            self.mute_state = MUTE_ST_ON
            dis.mute_on()
            mus.vol_mute_immediate()
            rel.mute_on()
            rel.deselect_all()

        else:
            self.mute_state = MUTE_ST_OFF
            dis.mute_off()
            rel.mute_off()          
            sel.select_immediate()   #update select with no change
            volume_left = vol.get_current_volume_left()
            volume_right = vol.get_current_volume_right()
            mus.vol_up_soft(volume_left, volume_right) 
        return
        
        
    def mute_on_soft(self):
        """Respond to message by turning on soft MUTE."""
        dis.mute_on()
        volume_left = vol.get_current_volume_left()
        volume_right = vol.get_current_volume_right()
        mus.vol_down_soft(volume_left, volume_right)
        rel.mute_on()
        self.mute_state = MUTE_ST_ON
        return
    
    def mute_on_soft_nodisplay(self):
        """Respond to message by turning on soft MUTE but don't update display - use in states where MUTE isn't shown on display."""
        #dis.mute_on()
        volume_left = vol.get_current_volume_left()
        volume_right = vol.get_current_volume_right()
        mus.vol_down_soft(volume_left, volume_right)
        rel.mute_on()
        self.mute_state = MUTE_ST_ON
        return
    
    
    def mute_off_soft(self):
        """Respond to message by turning off soft MUTE."""
        rel.mute_off()
        volume_left = vol.get_current_volume_left()
        volume_right = vol.get_current_volume_right()
        mus.vol_up_soft(volume_left, volume_right)        
        dis.mute_off()
        self.mute_state = MUTE_ST_OFF
        return
    
    def display_mute_state(self):
        if (self.mute_state == MUTE_ST_ON):
            dis.mute_on()
        else:
            dis.mute_off()
        return
        
            
        
class Operate():
    def __init__(self):
        self.operate_switch = operate_in.value()
        self.operate_switch_last = self.operate_switch
        self.operate_state = OPERATE_ST_OFF
        if (self.operate_switch == OPERATE_ON):
            self.mute_state = OPERATE_ST_ON
        return

    def change(self):
        self.operate_switch = operate_in.value()
        if ((self.operate_switch == OPERATE_ON) and (self.operate_switch_last == OPERATE_OFF)): #turn on event
            self.operate_switch_last = self.operate_switch
            self.mute_state = OPERATE_ST_ON
            return 1
        elif((self.operate_switch == OPERATE_OFF) and (self.operate_switch_last == OPERATE_ON)): #turn off event
            self.operate_switch_last = self.operate_switch
            self.operate_state = OPERATE_ST_OFF
            return 2
        else: # no change
            return 0
        
    def update_operate(self):  #update display
        #print("update_operate: self.operate_state is ", self.operate_state)
        if(self.operate_state == OPERATE_ST_ON):
            dis.operate_on()
        else:
            dis.operate_off()
        return
        
    def execute_operate(self):
        self.operate_switch = operate_in.value()
        self.operate_switch_last = self.operate_switch
        self.operate_state = OPERATE_ST_OFF
        if (self.operate_switch == OPERATE_ON):
            self.operate_state = OPERATE_ST_ON
        self.update_operate()    
        return
        
    def current_operate(self):   # same as execute_operate but returns the switch setting
        self.operate_switch = operate_in.value()
        self.operate_switch_last = self.operate_switch
        self.operate_state = OPERATE_ST_OFF
        if (self.operate_switch == OPERATE_ON):
            self.operate_state = OPERATE_ST_ON
        #self.update_operate()           
        return self.operate_state
        
        
    

class Display():
    def __init__(self):
        self.brightness = INITIAL_BRIGHTNESS
        self.change_brightness(0)
        self.clear_display()
        return
        
    
    def clear_display(self):
        buf = bytearray([REG_PREFIX, REG_CLEAR])
        i2c.writeto(DISPLAY_ADDR, buf)
        time.sleep_us(1500)
        return
    
    def set_brightness_standby(self):
        buf = bytearray([REG_PREFIX, REG_BRIGHTNESS, STANDBY_BRIGHTNESS])
        i2c.writeto(DISPLAY_ADDR, buf)
        time.sleep_us(100)
        return
    
    def change_brightness(self, change):
        if change < -1:
            print(f"Error: change_brightness can only change by -1, 0, 1 - input change was {change}")
            return
        if change > 1:
            print(f"Error: change_brightness can only change by -1, 0, 1 - input change was {change}")
            return
        self.brightness = self.brightness + change
        if self.brightness < 0:
            self.brightness = 0
        if self.brightness > MAX_BRIGHTNESS:
            self.brightness = MAX_BRIGHTNESS
        buf = bytearray([REG_PREFIX, REG_BRIGHTNESS, self.brightness])
        i2c.writeto(DISPLAY_ADDR, buf)
        time.sleep_us(100)
        return
    
    def display_brightness(self):
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray(f"      Display       ")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray(f"   Brightness: {self.brightness}")
        i2c.writeto(DISPLAY_ADDR, buf)
        return
    
    def display_volume(self, volume_left, volume_right):
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray('{:<2}'.format(volume_left) + "     Volume     " + '{:>2}'.format(volume_right))
        i2c.writeto(DISPLAY_ADDR, buf)  
        return


    def display_balance(self, balance_left, balance_right):
        
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray('{:<2}'.format(balance_left) + "     Balance    " + '{:>2}'.format(balance_right))
        i2c.writeto(DISPLAY_ADDR, buf)
        return


    def mute_on(self):
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4 + MUTE_POSITION])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("Mute")
        i2c.writeto(DISPLAY_ADDR, buf)
        return

    def mute_off(self):
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4 + MUTE_POSITION])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("    ")
        i2c.writeto(DISPLAY_ADDR, buf)
        return
    
    def operate_on(self):
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("Operate")
        i2c.writeto(DISPLAY_ADDR, buf)
        return
    
    def operate_off(self):
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("Standby")
        i2c.writeto(DISPLAY_ADDR, buf)
        return
    
    def display_select(self, input):
        # first clear the line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("                    ")
        i2c.writeto(DISPLAY_ADDR, buf)
        if (input == 1):
            buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
            i2c.writeto(DISPLAY_ADDR, buf)
            buf = bytearray(selector_info['1'])
            i2c.writeto(DISPLAY_ADDR, buf)
        elif(input == 2):
            buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
            i2c.writeto(DISPLAY_ADDR, buf)
            buf = bytearray(selector_info['2'])
            i2c.writeto(DISPLAY_ADDR, buf)
        elif(input == 3):
            buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
            i2c.writeto(DISPLAY_ADDR, buf)
            buf = bytearray(selector_info['3'])
            i2c.writeto(DISPLAY_ADDR, buf)
        elif(input == 4):
            buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
            i2c.writeto(DISPLAY_ADDR, buf)
            buf = bytearray(selector_info['4'])
            i2c.writeto(DISPLAY_ADDR, buf)
        elif(input == 5):
            buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
            i2c.writeto(DISPLAY_ADDR, buf)
            buf = bytearray(selector_info['5'])
            i2c.writeto(DISPLAY_ADDR, buf)
        else:
            buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
            i2c.writeto(DISPLAY_ADDR, buf)
            buf = bytearray("Unknown Input       ")
            i2c.writeto(DISPLAY_ADDR, buf)
        return

    def display_splash(self):   #intro screen
        #blank the screen
        dis.clear_display()
            
        #top line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("  4P1L Tube Preamp")
        i2c.writeto(DISPLAY_ADDR, buf)
            
        #line 2
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("Gingernut Labs 2022")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #line 2
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("MicroPython v1.19.1")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        
        #line4
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("  SW Version " + SW_VERSION)
        i2c.writeto(DISPLAY_ADDR, buf)
        return


    def filament_screen(self, count):
        #blank the screen
        dis.clear_display()
        
        #top line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("     Preheating")
        i2c.writeto(DISPLAY_ADDR, buf)

        #second line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("   Tube Filaments")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #third line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("    Please Wait")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #fourth line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("    " + '{:>2}'.format(count) + " seconds")
        i2c.writeto(DISPLAY_ADDR, buf)
        return


    def bplus_screen(self, count):
        #blank the screen
        dis.clear_display()
        
        #top line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("     Stabilizing")
        i2c.writeto(DISPLAY_ADDR, buf)

        #second line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE2])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("   B+ Power Supply")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #third line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("    Please Wait")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #fourth line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("    " + '{:>2}'.format(count) + " seconds")
        i2c.writeto(DISPLAY_ADDR, buf)
        return


    def standby_screen(self):
        self.clear_display()
        self.set_brightness_standby()
        buf = bytearray([REG_PREFIX, REG_POSITION, STANDBY_POSITION])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("STANDBY")
        i2c.writeto(DISPLAY_ADDR, buf)
        return


    def display_temp(self, temperature):
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3])
        i2c.writeto(DISPLAY_ADDR, buf)
        # had trouble figuring out how to write the degree sign, this is what I came up with
        degree_sign = 0xdf    # from Newhaven NHD-0420D3Z-NSW-BBW-V3 display font table
        capital_c = 0x43
        buf = bytearray("Temp " + str(temperature) + " ")
        buf.append(degree_sign)
        buf.append(capital_c) # can't append strings to bytearray so have to append the hex code
        i2c.writeto(DISPLAY_ADDR, buf)
        return

    def displayTubeTimer(self, tubeNumber, tubeActive, tubeAgeMin, tubeAgeHour):   # tube number, active, minutes, hours
        #blank the screen
        self.clear_display()
        
        #top line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE1])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("     Tube Timer")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #third line
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE3])
        i2c.writeto(DISPLAY_ADDR, buf)
        buf = bytearray("#  Act     Hr    Min")
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #tubeActiveLower = lower.tubeActive()
        if tubeActive == "yes":
            active = "Y"
        else:
            active = "N"
        buf = bytearray([REG_PREFIX, REG_POSITION, DISPLAY_LINE4])
        i2c.writeto(DISPLAY_ADDR, buf)
        
        #buf = bytearray(str(tubeNumber) + "   " + active + "     " + str(tubeAgeMin)+ "  " + str(tubeAgeHour))
        
        buf = bytearray(str(tubeNumber) + "   " + active + "   " + '{:>6}'.format(tubeAgeHour) + "    " + '{:>2}'.format(tubeAgeMin))
        i2c.writeto(DISPLAY_ADDR, buf)
        return




class Relay():

    def __init__(self):
        self.relay_array = [0 for x in range(16)]
        
        #print(self.relay_array)
        #self.relay_array[self.REL_FILAMENT] = self.REL_ON
        #print(self.relay_array)
        
        # bug in SPI interface, do initial write to get chip select correct
        self.mute_on()

        # initialize the relays - mute on, everything else off
        self.mute_on()
        self.deselect_all()
        # Then wait a bit and set them again in case they didn't get operated properly the first time
        # due to power-on conditions.
        time.sleep_ms(100)
        self.mute_on()
        self.deselect_all()
        return
    
    def write(self):
        #print("Entering write", self.relay_array)
        relays0 = 0x00
        relays1 = 0x00
        for i in range (0,8):
            relays0 = relays0 << 1
            if (self.relay_array[i] == 1):
                relays0 = relays0 | 0x01
            else:
                relays0 = relays0 | 0x00
        for i in range (8,16):
            relays1 = relays1 << 1
            if (self.relay_array[i] == 1):
                relays1 = relays1 | 0x01
            else:
                relays1 = relays1 | 0x00
        print ("relays0 and relays1 hex %x %x" % (relays0, relays1))
        buf = bytearray([relays0, relays1])
        spiCsRel.value(0)
        spiRel.write(buf)
        spiCsRel.value(1)
        return


    def filament_on(self):
        print ("Turning on Filament Relay")
        self.relay_array[REL_FILAMENT] = REL_ON
        self.write()
        return
    
    def filament_off(self):
        print ("Turning off Filament Relay")
        self.relay_array[REL_FILAMENT] = REL_OFF
        self.write()
        return

    def bplus_on(self):
        print ("Turning on B+ Relay")
        self.relay_array[REL_BPLUS] = REL_ON
        self.write()
        return
    
    def bplus_off(self):
        print ("Turning off B+ Relay")
        self.relay_array[REL_BPLUS] = REL_OFF
        self.write()
        return    
    
    def mute_on(self):
        print ("Turning on Mute Relay")
        self.relay_array[REL_MUTE] = REL_ON
        self.write()
        return
    
    def mute_off(self):
        print ("Turning off Mute Relay")
        self.relay_array[REL_MUTE] = REL_OFF
        self.write()
        return   

    # this function takes a command plus the current relay state and returns a possibly new relay state.
    def deselect_all(self):
        self.relay_array[REL_SEL1RESET] = REL_ON
        self.relay_array[REL_SEL2RESET] = REL_ON
        self.relay_array[REL_SEL3RESET] = REL_ON
        self.relay_array[REL_SEL4RESET] = REL_ON
        self.relay_array[REL_SEL5RESET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)  # wait for latching relays to take their set then de-energize all latching relays.
        self.relay_array[REL_SEL1RESET] = REL_OFF
        self.relay_array[REL_SEL2RESET] = REL_OFF
        self.relay_array[REL_SEL3RESET] = REL_OFF
        self.relay_array[REL_SEL4RESET] = REL_OFF
        self.relay_array[REL_SEL5RESET] = REL_OFF 
        self.write()
        return

    def select(self, input_select):
        #first have to deselect whatever was already selected then give a bit of time to settle
        self.deselect_all()
        time.sleep_ms(REL_LATCH_TIME)
        if (input_select == SELECT_STREAMING):
            self.select_streaming()
        elif(input_select == SELECT_CD):
            self.select_cd()
        elif(input_select == SELECT_PHONO):
            self.select_phono()
        elif(input_select == SELECT_AUX1):
            self.select_aux1()
        elif(input_select == SELECT_AUX2):
            self.select_aux2()
        return

    def select_streaming(self):
        self.relay_array[REL_SEL1SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL1SET] = REL_OFF
        self.write()
        return
    
    def select_cd(self):
        self.relay_array[REL_SEL2SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL2SET] = REL_OFF
        self.write()
        return

    def select_phono(self):
        self.relay_array[REL_SEL3SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL3SET] = REL_OFF
        self.write()
        return
    
    def select_aux1(self):
        self.relay_array[REL_SEL4SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL4SET] = REL_OFF
        self.write()
        return

    def select_aux2(self):
        self.relay_array[REL_SEL5SET] = REL_ON
        self.write()
        time.sleep_ms(REL_LATCH_TIME)
        self.relay_array[REL_SEL5SET] = REL_OFF
        self.write()
        return



class Muses72320():
    def __init__(self):
        self.vol_left = 0
        self.vol_right = 0
        self.write(self.vol_left, self.vol_right)
        return

    def write(self, left, right):
        """Method to write the volume data to the left and right volume chips"""
        #calculate left chip data to write, value has been checked for bounds before call to this method
        data_left = MUSES_ATTEN_0 + 2*(MAX_VOLUME - left)
        if (left == 0):
            data_left = 0xff  #mute    
        print("Volume chip data left channel is ", data_left)
        
        #calculate right chip data to write, value has been checked for bounds before call to this method
        data_right = MUSES_ATTEN_0 + 2*(MAX_VOLUME - right)
        if (right == 0):
            data_right = 0xff  #mute
        
        #now do the writes to the chips- the chip selects are done in SW here, the SPI device does the HW signal wiggling.
        buf = bytearray([data_left, LEFT_LSB_0])
        spiCsVol.value(0)
        spiVol.write(buf)
        spiCsVol.value(1)
        
        buf = bytearray([data_left, LEFT_LSB_1])
        spiCsVol.value(0)
        spiVol.write(buf)
        spiCsVol.value(1)
        
        buf = bytearray([data_right, RIGHT_LSB_0])
        spiCsVol.value(0)
        spiVol.write(buf)
        spiCsVol.value(1)
        
        buf = bytearray([data_right, RIGHT_LSB_1])
        spiCsVol.value(0)
        spiVol.write(buf)
        spiCsVol.value(1)
        return

    def vol_down_soft(self, left, right):
        #print("In vol_down_soft, left is ", left)
        largest = left
        if (right > largest):
            largest = right 
        while (largest > 0):
            if (left > 0):
                left -= 1
            if (right > 0):
                right -= 1
            #print("largest is, writing to chips ", largest, left, right)
            self.write(left, right)
            largest -= 1
            time.sleep_ms(4)
        return
        
    def vol_up_soft(self, left, right):
        #print("In vol_up_soft, left is ", left)
        largest = left
        if (right > largest):
            largest = right
        lvol = 0
        rvol = 0
        while (largest > 0):
            if (lvol < left):
                lvol += 1
            if (rvol < right):
                rvol += 1
            #print("largest is, writing to chips ", largest, lvol, rvol)
            self.write(lvol, rvol)
            largest -= 1
            time.sleep_ms(4)
        return        

    def vol_mute_immediate(self):
        """volume chips to 0 with no delay"""
        self.write(0,0)
        return


class MPC9808():
    def __init__(self):
        self.temp = 0x0000        # raw register read value
        self.temperature = 0      # calculated temperature
        self.update()
        return
        
    def update(self):
        self.read()
        self.calculate()
        self.display()
        return
         
    def read(self):
        buf = bytearray([TEMP_DATA_REG])
        readbuf = bytearray(2)
        i2c.writeto(MPC9808_ADDR, buf)
        readbuf = i2c.readfrom(MPC9808_ADDR, 2)
        #print("returned temperature data:", readbuf)
        self.temp = readbuf[0]
        self.temp = self.temp << 8
        self.temp = self.temp + readbuf[1]
        #print("returning temp variable is hex: %x" % (self.temp))
        return
    
    def calculate(self):
        self.temperature = self.temp
        if ((self.temperature & 0x1000) == 0x1000):  #sign bit is set, so T < 0C
            #print("Temp is below 0C")
            self.temperature = self.temperature & 0x0FFF  #clear flags and sign
            self.temperature = self.temperature >> 4
            self.temperature = 256 - self.temperature
        else:
            #print("Temp is above 0C")
            self.temperature = self.temperature & 0x0FFF  #clear flags and sign - sign was already 0
            self.temperature = self.temperature >> 4
        #print("Temperature is %i C" % (self.temperature))
        return
    
    def display(self):
        dis.display_temp(self.temperature)
        return
    
    def change(self):
        readval = 0x0000
        buf = bytearray([TEMP_DATA_REG])
        readbuf = bytearray(2)
        i2c.writeto(MPC9808_ADDR, buf)
        readbuf = i2c.readfrom(MPC9808_ADDR, 2)
        readval = readbuf[0]
        readval = readval << 8
        readval = readval + readbuf[1]
        return (readval>>4) - (self.temp>>4)   # return nonzero if whole degree or sign has changed
    
    
class TubeTimer():
    def __init__(self):
        self.timer = 0
        self.minutes = 0
        self.data = []
        
        self.headingNumber = 0
        self.headingActive = 0
        self.headingAgeMin = 0
        self.headingAgeHour = 0
        
        self.displayTube = 1
        return
    
    
    # later can delete this and make a coroutine that does only minute updates and calls addMinute, that will reduce the
    # second-based processing.  Just using this now so I can see things execute.
    def addSecond(self):
        self.timer = self.timer + 1
        #print("time in seconds ", self.timer)
        if ((self.timer % 10) == 0):
            self.addMinute()
        return
    
    def addMinute(self):
        self.minutes = self.minutes + 1
        print("minutes timer is ", self.minutes)
        self.incTubeData()
        return
    
    def readTubeData(self):
        tubeAge = 0
        i=0
        with open("tubeData.csv", "r") as file:
            #print("reading the tube data from the csv file")
            self.data.clear()
            for lineStr in file:
                lineStr=lineStr.rstrip("\n")
                lineStr=lineStr.rstrip("\r")
                self.data.append(lineStr.split(","))
                #print("list of data on one line read from file",self.data[i])
                i+=1
            
        #find which column has the tube number
        i=0
        for heading in self.data[0]:
            if (heading == "number"):
                self.headingNumber = i
                #print("the number heading is", self.headingNumber)
            i=i+1
            
        #find which column has the "active" data (tube is in the amp and needs its age data updated in real time)
        i=0
        for heading in self.data[0]:
            if (heading == "active"):
                self.headingActive = i
                #print("the active heading is", self.headingActive)
            i=i+1
                
        #find which column has ageMin - the age in minutes
        i=0
        for heading in self.data[0]:
            if (heading == "ageMin"):
                self.headingAgeMin = i
                #print("the ageMin heading is", self.headingAgeMin)
            i=i+1                       
            
        #find which column has ageHour - the age in hours
        i=0
        for heading in self.data[0]:
            if (heading == "ageHour"):
                self.headingAgeHour = i
                #print("the ageHour heading is", self.headingAgeHour)
            i=i+1                       
        return
        
        
    def incTubeData(self):
        
        self.readTubeData()
        for lineList in self.data:
            if(lineList[self.headingActive] == "yes"):
                #print(f"lineList is {lineList}")
                tubeAgeMin = int(lineList[self.headingAgeMin]) + 1
                #print(f"tubeAgeMin is {tubeAgeMin}")
                lineList[self.headingAgeMin] = str(tubeAgeMin)
                if (tubeAgeMin >= 60):
                    lineList[self.headingAgeMin] = "0"
                    lineList[self.headingAgeHour] = str(int(lineList[self.headingAgeHour]) + 1)
                #print("updating tube", lineList[self.headingNumber], "to", lineList[self.headingAgeMin], "minutes and",lineList[self.headingAgeHour], "hours")
        self.writeTubeData()
        return
    
    
    def writeTubeData(self):
        with open ("tubeData.csv", "w") as outputFile:
            for lineList in self.data:
                writeLine = lineList[self.headingNumber] + "," + lineList[self.headingActive] + "," + lineList[self.headingAgeMin] + "," + lineList[self.headingAgeHour] + "\n"
                #print(writeLine)
                outputFile.write(writeLine)
        outputFile.close()
        return
    
    
    def show_tt(self, change):
        self.readTubeData()
        self.displayTube = self.displayTube + change
        
        #print("In show_tt, change is", change)
        
        if self.displayTube < 1:
            self.displayTube = 1
        if self.displayTube > len(self.data):
            self.displayTube = len(self.data)
        
        #print("self.displayTube is", self.displayTube)
        
        i=0
        for lineList in self.data:
            if (i > 0):
                tubeNum = int(lineList[self.headingNumber])
                #print ("tubeNum", tubeNum)
                if (tubeNum == self.displayTube):
                    #print("in here, numbers are ", self.displayTube)
                    dis.displayTubeTimer(tubeNum, lineList[self.headingActive], lineList[self.headingAgeMin], lineList[self.headingAgeHour])   # tube number, active, minutes, hours
            i = i+1
        return
    
    


class State():
    
    def __init__(self):
        self.state = STATE_STARTUP
        self.splash_count = SPLASH_DELAY
        self.filament_count = FILAMENT_DELAY
        self.bplus_count = BPLUS_DELAY
        return
    
    def dispatch(self, message):
        """This function dispatches a task to perform based upon what the message was - time based event or input event."""
        
        if self.state == STATE_OPERATE:
            if message == VOL_KNOB_CW:
                vol.update_volume(1)
            elif message == VOL_KNOB_CCW:
                vol.update_volume(-1)
            elif message == SEL_KNOB_CW:
                sel.update_select(1)
            elif message == SEL_KNOB_CCW:
                sel.update_select(-1)
            elif message == SECOND_BEAT:
                tmp.update()
            elif message == MINUTE_BEAT:
                tim.addMinute()
            elif message == SW_MUTE_ON:
                mut.mute_on_soft()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == L_PB_PUSHED:
                self.operate_to_bal()
            elif message == SW_OPERATE_OFF:
                self.goto_standby()
        
        #basically the same as operate but adjusts balance with left knob and use right PB to go back to STATE_OPERATE
        elif self.state == STATE_BALANCE:            
            if message == VOL_KNOB_CW:
                vol.update_balance(1)
            elif message == VOL_KNOB_CCW:
                vol.update_balance(-1)
            elif message == SEL_KNOB_CW:
                sel.update_select(1)
            elif message == SEL_KNOB_CCW:
                sel.update_select(-1)
            elif message == SECOND_BEAT:
                tmp.update()
            elif message == MINUTE_BEAT:
                tim.addMinute()
            elif message == SW_MUTE_ON:
                mut.mute_on_soft()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == R_PB_PUSHED:
                self.bal_to_operate()
            elif message == L_PB_PUSHED:
                self.bal_to_tt_display()
            elif message == SW_OPERATE_OFF:
                self.goto_standby()
        
        elif self.state == STATE_STANDBY:
            if message == SW_OPERATE_ON:
                self.goto_filament()
        
        elif self.state == STATE_FILAMENT:
            if message == SW_OPERATE_OFF:
                self.goto_standby()
            elif message == SECOND_BEAT:
                self.st_filament() 
                    
        elif self.state == STATE_BPLUS:
            if message == SW_OPERATE_OFF:
                self.goto_standby()
            elif message == SECOND_BEAT:
                self.st_bplus()
                
        elif self.state == STATE_STARTUP:
            if message == SECOND_BEAT:
                self.st_splash()
                
        elif self.state == STATE_TT_DISPLAY:
            if message == VOL_KNOB_CW:
                tim.show_tt(1)
            elif message == VOL_KNOB_CCW:
                tim.show_tt(-1)
            elif message == MINUTE_BEAT:
                tim.addMinute()
                tim.show_tt(0)
            elif message == R_PB_PUSHED:
                self.goto_operate()
            elif message == L_PB_PUSHED:
                self.tt_dis_to_bright()
            elif message == SW_MUTE_ON:
                mut.mute_on_soft_nodisplay()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == SW_OPERATE_OFF:
                self.goto_standby()
                
        elif self.state == STATE_BRIGHTNESS:
            if message == VOL_KNOB_CW:
                dis.change_brightness(1)
                dis.display_brightness()
            elif message == VOL_KNOB_CCW:
                dis.change_brightness(-1)
                dis.display_brightness()
            elif message == R_PB_PUSHED:
                self.goto_operate()
            elif message == SW_MUTE_ON:
                mut.mute_on_soft_nodisplay()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == SW_OPERATE_OFF:
                self.goto_standby()


        return
        
        
    def goto_standby(self):
        mut.force_mute()
        rel.bplus_off()
        rel.filament_off()
        dis.standby_screen()
        self.state = STATE_STANDBY
        return
    
    
    def goto_filament(self):
        self.filament_count = FILAMENT_DELAY
        dis.filament_screen(filament_count)
        rel.filament_on()
        self.state = STATE_FILAMENT
        return
        
        
    def st_splash(self):
        """Display the splash screen."""
        self.splash_count = self.splash_count - 1
        if self.splash_count == 0:
            self.splash_count = SPLASH_DELAY
            if (OPERATE_ST_ON == op.current_operate()):
                rel.filament_on()
                self.filament_count = FILAMENT_DELAY
                dis.filament_screen(self.filament_count)
                self.state = STATE_FILAMENT
            else:
                self.goto_standby()
        return
        
        
    def st_filament(self):
        """Operate the filament preheat routine."""
        self.filament_count -= 1
        dis.filament_screen(self.filament_count)
        if self.filament_count == 0:
            self.bplus_count = BPLUS_DELAY
            dis.bplus_screen(self.bplus_count)
            rel.bplus_on()
            self.state = STATE_BPLUS
        return
    
    
    def st_bplus(self):
        """Operate the Bplus supply stabilization routine."""
        self.bplus_count -= 1
        dis.bplus_screen(self.bplus_count)
        if self.bplus_count == 0:
            if (OPERATE_ST_ON == op.current_operate()):
                dis.clear_display()
                dis.operate_on()
                dis.display_select(sel.get_current_select())
                vol.update_volume(0)
                tmp.update()
                mut.mute_immediate()
                self.state = STATE_OPERATE
            else:
                dis.clear_display()
                vol.update_volume(0)   #update the volume with no change
                sel.update_select(0)   #update select with no change
                mut.force_mute()
                dis.standby_screen()
                self.state = STATE_STANDBY
        return
        
        
    def operate_to_bal(self):
        """Transition from STATE_OPERATE to STATE_BALANCE, where the balance can be adjusted."""
        vol.update_balance(0)
        self.state = STATE_BALANCE
        return
    
    def bal_to_operate(self):
        """Transition from STATE_BALANCE to STATE_OPERATE, which is the main state."""
        vol.update_volume(0)
        self.state = STATE_OPERATE
        return
        

    def bal_to_tt_display(self):
        tim.show_tt(0)
        self.state = STATE_TT_DISPLAY
        return
    
    def goto_operate(self):
        dis.clear_display()
        dis.operate_on()
        vol.update_volume(0)
        dis.display_select(sel.get_current_select())
        mut.display_mute_state()
        tmp.update()
        self.state = STATE_OPERATE
        return
    
    def tt_dis_to_bright(self):
        dis.clear_display()
        dis.display_brightness()
        self.state = STATE_BRIGHTNESS
        return



    
    
        
###################################################################
# Initialize Devices
led = machine.Pin(25, Pin.OUT)
i2c = machine.I2C(1, scl=Pin(27), sda=Pin(26), freq=50_000)
spiVol = machine.SPI(0, baudrate=100_000, polarity=1, phase=0, bits=8, firstbit=machine.SPI.MSB, sck=Pin(18), mosi=Pin(19), miso=Pin(20)) #pin 20 not needed but apparently must be delcared
spiCsVol = Pin(21, machine.Pin.OUT)
spiRel = machine.SPI(1, baudrate=200_000, polarity=0, phase=0, bits=8, firstbit=machine.SPI.MSB, sck=Pin(10), mosi=Pin(11), miso=Pin(12)) #pin 20 not needed but apparently must be delcared
spiCsRel = Pin(13, machine.Pin.OUT)



###################################################################
# Initialization Code

print ("Vol0 Encoder Input pin 7:", vol0_in.value())
print ("Vol1 Encoder Input pin 9:", vol1_in.value())
print ("Sel0 Encoder Input pin 2:", sel0_in.value())
print ("Sel1 Encoder Input pin 3:", sel1_in.value())

spiCsVol.value(1)
spiCsRel.value(0)


#scan for the I2C devices
devices = i2c.scan()
if (devices):
    for d in devices:
        if (d == DISPLAY_ADDR):
            print("Found LCD display at address", hex(d))
        elif(d == MPC9808_ADDR):
            print("Found MPC9808 temp sensor at address", hex(d))
        else:
            print("ERROR: Found I2C device at address", hex(d))       
else:
    print("FAIL: no I2C devices found!!!")

# get the selector information from json file

default_selections = '{"1": "Input 1", "2": "Input 2", "3": "Input 3", "4": "Input 4", "5": "Input 5"}'

try:
    with open('selector.json', 'r') as f:
        selector_info = json.load(f)
except ValueError:
    selector_info = json.loads(default_selections)
    print('Error: Invalid JSON data file selector.json, using default selection strings')



#pb = Pushbutton()
vol_enc = Vol_encoder()
vol = Volume()
dis = Display()
mut = Mute()
sel = Sel_encoder()
rel = Relay()
op =  Operate()
mus = Muses72320()
tmp = MPC9808()
tim = TubeTimer()
q   = queue.Queue(32)
st  = State()


# set initial state
state = STATE_STARTUP
loop_counter = 0
filament_count = FILAMENT_DELAY
bplus_count = BPLUS_DELAY


async def seconds_beat():
    """A message every second for any job that needs to be done on a one second time base."""
    while True:
        await q.put(SECOND_BEAT)
        await uasyncio.sleep_ms(1000)
    return


async def minutes_beat():
    """A message every second for any job that needs to be done on a one second time base."""
    while True:
        await q.put(MINUTE_BEAT)
        await uasyncio.sleep(60)
    return


async def l_pb_input():
    """Detects that the left pushbutton switch has been depressed.  Debouncing is done here."""
    btn_current = volpb_in.value()
    btn_last = btn_current
    while True:
        btn_current = volpb_in.value()
        if (btn_current == PB_PUSHED) and (btn_last == PB_RELEASED):
            await q.put(L_PB_PUSHED)
        btn_last = btn_current
        await uasyncio.sleep(0.05)
    return
        

async def r_pb_input():
    """Detects that the right pushbutton switch has been depressed.  Debouncing is done here."""
    btn_current = selpb_in.value()
    btn_last = btn_current
    while True:
        btn_current = selpb_in.value()
        if (btn_current == PB_PUSHED) and (btn_last == PB_RELEASED):
            await q.put(R_PB_PUSHED)
        btn_last = btn_current
        await uasyncio.sleep(0.08)
    return


async def vol_rotated():
    """Detects that the VOLUME (left) quadrature encoder has been rotated, there is a different message for CW or CCW rotation by 1 unit.  Debouncing is done here."""
    while True:
        knob_current = vol_enc.change()
        if knob_current == 1:
            await q.put(VOL_KNOB_CW)
        elif knob_current == -1:
            await q.put(VOL_KNOB_CCW)
        await uasyncio.sleep(0.01)
    return

async def sel_rotated():
    """Detects that the SELECT (right) quadrature encoder has been rotated, there is a different message for CW or CCW rotation by 1 unit.  Debouncing is done here."""
    while True:
        knob_current = sel.change()
        if knob_current == 1:
            await q.put(SEL_KNOB_CW)
        elif knob_current == -1:
            await q.put(SEL_KNOB_CCW)
        await uasyncio.sleep(0.01)
    return


async def operate_input():
    """Detects that the OPERATE switch has changed state, sends the appropriate message to the queue in response."""
    operate_current = operate_in.value()
    operate_last = operate_current
    while True:
        operate_current = operate_in.value()
        if (operate_current == OPERATE_ON) and (operate_last == OPERATE_OFF):
            # switch was just turned on
            await q.put(SW_OPERATE_ON)
        elif (operate_current == OPERATE_OFF) and (operate_last == OPERATE_ON):
            # switch was just turned off
            await q.put(SW_OPERATE_OFF)
        operate_last = operate_current
        await uasyncio.sleep(0.10)
    return


async def mute_input():
    """Detects that the MUTE switch has changed state, sends the appropriate message to the queue in response."""
    mute_current = mute_in.value()
    mute_last = mute_current
    while True:
        mute_current = mute_in.value()
        if (mute_current == MUTE_ON) and (mute_last == MUTE_OFF):
            # switch was just turned on
            await q.put(SW_MUTE_ON)
        elif (mute_current == MUTE_OFF) and (mute_last == MUTE_ON):
            # switch was just turned off
            await q.put(SW_MUTE_OFF)
        mute_last = mute_current
        await uasyncio.sleep(0.10)
    return



###################################################################
# Main program loop - core 0 (note sure which core but we'll call this one #0)
#async def amp_body():
async def amp_body():
    global state
    global splash_count
    global filament_count
    global bplus_count
    global loop_counter
    
    #create coroutines to detect button pushes
    uasyncio.create_task(l_pb_input())
    uasyncio.create_task(r_pb_input())
    
    #create coroutines to detect knobs turned
    uasyncio.create_task(vol_rotated())
    uasyncio.create_task(sel_rotated())
    
    #create coroutines to detect toggle switch changes
    uasyncio.create_task(operate_input())
    uasyncio.create_task(mute_input())
    
    #create coroutine with time-based beats
    uasyncio.create_task(seconds_beat())
    uasyncio.create_task(minutes_beat())
    
    
    dis.display_splash()
    
    while True:
        if not q.empty():
            message = await q.get()
            #print("message from queue: ", message)
            st.dispatch(message)
        await uasyncio.sleep_ms(10)
    return

uasyncio.run(amp_body())
    
###################################################################
# start main asyncio scheduler
# async def main():
#     task1 = uasyncio.create_task(amp_body())
#     #task2 = uasyncio.create_task(blink_led())
#     task2 = uasyncio.create_task(_thread.start_new_thread(blink_led()))
#     
#     await task1
#     await task2
# 
# 
# uasyncio.run(main())
