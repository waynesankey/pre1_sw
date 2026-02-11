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
        volume_old = self.volume
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
        return self.volume != volume_old

    def update_balance(self, balance_change):
        balance_old = self.balance
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
        return self.balance != balance_old

    def set_volume(self, volume):
        volume_old = self.volume
        self.volume = max(0, min(volume, MAX_VOLUME))
        self.volume_left = self.volume - self.balance
        self.volume_right = self.volume + self.balance
        self.volume_left = max(0, min(self.volume_left, MAX_VOLUME))
        self.volume_right = max(0, min(self.volume_right, MAX_VOLUME))
        self.dis.display_volume(self.volume_left, self.volume_right)
        self.mus.write(self.volume_left, self.volume_right)
        return self.volume != volume_old

    def set_balance(self, balance):
        balance_old = self.balance
        self.balance = max(-MAX_BALANCE, min(balance, MAX_BALANCE))
        self.balance_left = 0 - self.balance
        self.balance_right = self.balance
        self.volume_left = self.volume + self.balance_left
        self.volume_right = self.volume + self.balance_right
        self.dis.display_balance(self.balance_left, self.balance_right)
        self.mus.write(self.volume_left, self.volume_right)
        return self.balance != balance_old

    def set_state(self, volume, balance):
        self.volume = max(0, min(volume, MAX_VOLUME))
        self.balance = max(-MAX_BALANCE, min(balance, MAX_BALANCE))
        self.balance_left = 0 - self.balance
        self.balance_right = self.balance
        self.volume_left = self.volume + self.balance_left
        self.volume_right = self.volume + self.balance_right
        self.volume_left = max(0, min(self.volume_left, MAX_VOLUME))
        self.volume_right = max(0, min(self.volume_right, MAX_VOLUME))

    def get_current_volume(self):
        return self.volume

    def get_current_balance(self):
        return self.balance

    def get_current_volume_left(self):
        return self.volume_left

    def get_current_volume_right(self):
        return self.volume_right
