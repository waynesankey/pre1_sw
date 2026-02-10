from config import *


class Mute:
    def __init__(self, mute_pin, dis_obj, vol_obj, mus_obj, rel_obj, sel_obj):
        self.mute_pin = mute_pin
        self.dis = dis_obj
        self.vol = vol_obj
        self.mus = mus_obj
        self.rel = rel_obj
        self.sel = sel_obj

        self.mute_switch = self.mute_pin.value()
        self.mute_switch_last = self.mute_switch
        self.mute_state = MUTE_ST_OFF
        if self.mute_switch == MUTE_ON:
            self.mute_state = MUTE_ST_ON

    def update_mute(self):
        print("update_mute: self.mute_state is", self.mute_state)
        if self.mute_state == MUTE_ST_ON:
            self.dis.mute_on()
            volume_left = self.vol.get_current_volume_left()
            volume_right = self.vol.get_current_volume_right()
            self.mus.vol_down_soft(volume_left, volume_right)
            self.rel.mute_on()
        else:
            self.rel.mute_off()
            volume_left = self.vol.get_current_volume_left()
            volume_right = self.vol.get_current_volume_right()
            self.mus.vol_up_soft(volume_left, volume_right)
            self.dis.mute_off()

    def force_mute(self):
        self.mute_state = MUTE_ST_ON
        self.update_mute()

    def mute_immediate(self):
        self.mute_switch = self.mute_pin.value()
        self.mute_switch_last = self.mute_switch
        if self.mute_switch == MUTE_ON:
            self.mute_state = MUTE_ST_ON
            self.dis.mute_on()
            self.mus.vol_mute_immediate()
            self.rel.mute_on()
            self.rel.deselect_all()
        else:
            self.mute_state = MUTE_ST_OFF
            self.dis.mute_off()
            self.rel.mute_off()
            self.sel.select_immediate()
            volume_left = self.vol.get_current_volume_left()
            volume_right = self.vol.get_current_volume_right()
            self.mus.vol_up_soft(volume_left, volume_right)

    def mute_on_soft(self):
        self.dis.mute_on()
        volume_left = self.vol.get_current_volume_left()
        volume_right = self.vol.get_current_volume_right()
        self.mus.vol_down_soft(volume_left, volume_right)
        self.rel.mute_on()
        self.mute_state = MUTE_ST_ON

    def mute_on_soft_nodisplay(self):
        volume_left = self.vol.get_current_volume_left()
        volume_right = self.vol.get_current_volume_right()
        self.mus.vol_down_soft(volume_left, volume_right)
        self.rel.mute_on()
        self.mute_state = MUTE_ST_ON

    def mute_off_soft(self):
        self.rel.mute_off()
        volume_left = self.vol.get_current_volume_left()
        volume_right = self.vol.get_current_volume_right()
        self.mus.vol_up_soft(volume_left, volume_right)
        self.dis.mute_off()
        self.mute_state = MUTE_ST_OFF

    def display_mute_state(self):
        if self.mute_state == MUTE_ST_ON:
            self.dis.mute_on()
        else:
            self.dis.mute_off()
