from config import *


class Selector:
    def __init__(self, vol_obj, mus_obj, dis_obj, rel_obj):
        self.select = SELECT_STREAMING
        self.vol = vol_obj
        self.mus = mus_obj
        self.dis = dis_obj
        self.rel = rel_obj

    def update_select(self, select_change):
        print("Entering update_select,current select is %i and change is %i" % (self.select, select_change))
        self.select = self.select + select_change
        if self.select < SELECT_STREAMING:
            self.select = SELECT_STREAMING
            return
        if self.select > SELECT_AUX2:
            self.select = SELECT_AUX2
            return

        print("In update_select, new select is", self.select)
        volume_left = self.vol.get_current_volume_left()
        volume_right = self.vol.get_current_volume_right()
        self.mus.vol_down_soft(volume_left, volume_right)
        self.dis.display_select(self.select)
        self.rel.select(self.select)
        self.mus.vol_up_soft(volume_left, volume_right)

    def select_immediate(self):
        self.dis.display_select(self.select)
        self.rel.select(self.select)

    def get_current_select(self):
        return self.select
