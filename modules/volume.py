from config import *


class Volume:
    def __init__(self, dis_obj, mus_obj):
        self.volume = 0
        self.balance = 0
        self.volume_left = 0
        self.volume_right = 0
        self.balance_left = 0
        self.balance_right = 0
        self.dis = dis_obj
        self.mus = mus_obj

    def update_volume(self, volume_change):
        self.volume = self.volume + volume_change
        if self.volume < 0:
            self.volume = 0
        if self.volume > MAX_VOLUME:
            self.volume = MAX_VOLUME

        self.volume_left = self.volume - self.balance
        self.volume_right = self.volume + self.balance

        if self.volume_left < 0:
            self.volume_left = 0
        if self.volume_right < 0:
            self.volume_right = 0
        if self.volume_left > MAX_VOLUME:
            self.volume_left = MAX_VOLUME
        if self.volume_right > MAX_VOLUME:
            self.volume_right = MAX_VOLUME

        self.dis.display_volume(self.volume_left, self.volume_right)
        self.mus.write(self.volume_left, self.volume_right)

    def update_balance(self, balance_change):
        self.balance = self.balance + balance_change
        if self.balance < (0 - MAX_BALANCE):
            self.balance = 0 - MAX_BALANCE
        if self.balance > MAX_BALANCE:
            self.balance = MAX_BALANCE

        self.balance_left = 0 - self.balance
        self.balance_right = self.balance
        self.volume_left = self.volume + self.balance_left
        self.volume_right = self.volume + self.balance_right

        self.dis.display_balance(self.balance_left, self.balance_right)
        self.mus.write(self.volume_left, self.volume_right)

    def get_current_volume_left(self):
        return self.volume_left

    def get_current_volume_right(self):
        return self.volume_right
