from config import *


class Operate:
    def __init__(self, operate_pin):
        self.operate_pin = operate_pin
        self.operate_switch = self.operate_pin.value()
        self.operate_switch_last = self.operate_switch
        self.operate_state = OPERATE_ST_OFF
        if self.operate_switch == OPERATE_ON:
            self.operate_state = OPERATE_ST_ON

    def current_operate(self):
        self.operate_switch = self.operate_pin.value()
        self.operate_switch_last = self.operate_switch
        self.operate_state = OPERATE_ST_OFF
        if self.operate_switch == OPERATE_ON:
            self.operate_state = OPERATE_ST_ON
        return self.operate_state
