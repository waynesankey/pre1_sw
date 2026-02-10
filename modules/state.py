from config import *


class State:
    def __init__(self):
        self.state = STATE_STARTUP
        self.splash_count = SPLASH_DELAY
        self.filament_count = FILAMENT_DELAY
        self.bplus_count = BPLUS_DELAY

    def dispatch(self, message, vol, sel, mut, dis, rel, op, tmp, tim):
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
                tim.add_minute()
            elif message == SW_MUTE_ON:
                mut.mute_on_soft()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == L_PB_PUSHED:
                self.operate_to_bal(vol)
            elif message == SW_OPERATE_OFF:
                self.goto_standby(mut, rel, dis)

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
                tim.add_minute()
            elif message == SW_MUTE_ON:
                mut.mute_on_soft()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == R_PB_PUSHED:
                self.bal_to_operate(vol)
            elif message == L_PB_PUSHED:
                self.bal_to_tt_display(tim)
            elif message == SW_OPERATE_OFF:
                self.goto_standby(mut, rel, dis)

        elif self.state == STATE_STANDBY:
            if message == SW_OPERATE_ON:
                self.goto_filament(dis, rel)

        elif self.state == STATE_FILAMENT:
            if message == SW_OPERATE_OFF:
                self.goto_standby(mut, rel, dis)
            elif message == SECOND_BEAT:
                self.st_filament(dis, rel)

        elif self.state == STATE_BPLUS:
            if message == SW_OPERATE_OFF:
                self.goto_standby(mut, rel, dis)
            elif message == SECOND_BEAT:
                self.st_bplus(vol, sel, mut, dis, rel, op, tmp)

        elif self.state == STATE_STARTUP:
            if message == SECOND_BEAT:
                self.st_splash(dis, rel, op, mut)

        elif self.state == STATE_TT_DISPLAY:
            if message == VOL_KNOB_CW:
                tim.show_tt(1)
            elif message == VOL_KNOB_CCW:
                tim.show_tt(-1)
            elif message == MINUTE_BEAT:
                tim.add_minute()
                tim.show_tt(0)
            elif message == R_PB_PUSHED:
                self.goto_operate(vol, sel, mut, dis, tmp)
            elif message == L_PB_PUSHED:
                self.tt_dis_to_bright(dis)
            elif message == SW_MUTE_ON:
                mut.mute_on_soft_nodisplay()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == SW_OPERATE_OFF:
                self.goto_standby(mut, rel, dis)

        elif self.state == STATE_BRIGHTNESS:
            if message == VOL_KNOB_CW:
                dis.change_brightness(1)
                dis.display_brightness()
            elif message == VOL_KNOB_CCW:
                dis.change_brightness(-1)
                dis.display_brightness()
            elif message == MINUTE_BEAT:
                tim.add_minute()
            elif message == R_PB_PUSHED:
                self.goto_operate(vol, sel, mut, dis, tmp)
            elif message == SW_MUTE_ON:
                mut.mute_on_soft_nodisplay()
            elif message == SW_MUTE_OFF:
                mut.mute_off_soft()
            elif message == SW_OPERATE_OFF:
                self.goto_standby(mut, rel, dis)

    def goto_standby(self, mut, rel, dis):
        mut.force_mute()
        rel.bplus_off()
        rel.filament_off()
        dis.standby_screen()
        self.state = STATE_STANDBY

    def goto_filament(self, dis, rel):
        self.filament_count = FILAMENT_DELAY
        dis.filament_screen(self.filament_count)
        rel.filament_on()
        self.state = STATE_FILAMENT

    def st_splash(self, dis, rel, op, mut):
        self.splash_count = self.splash_count - 1
        if self.splash_count == 0:
            self.splash_count = SPLASH_DELAY
            if OPERATE_ST_ON == op.current_operate():
                rel.filament_on()
                self.filament_count = FILAMENT_DELAY
                dis.filament_screen(self.filament_count)
                self.state = STATE_FILAMENT
            else:
                self.goto_standby(mut, rel, dis)

    def st_filament(self, dis, rel):
        self.filament_count -= 1
        dis.filament_screen(self.filament_count)
        if self.filament_count == 0:
            self.bplus_count = BPLUS_DELAY
            dis.bplus_screen(self.bplus_count)
            rel.bplus_on()
            self.state = STATE_BPLUS

    def st_bplus(self, vol, sel, mut, dis, rel, op, tmp):
        self.bplus_count -= 1
        dis.bplus_screen(self.bplus_count)
        if self.bplus_count == 0:
            if OPERATE_ST_ON == op.current_operate():
                dis.clear_display()
                dis.operate_on()
                dis.display_select(sel.get_current_select())
                vol.update_volume(0)
                tmp.update()
                mut.mute_immediate()
                self.state = STATE_OPERATE
            else:
                dis.clear_display()
                vol.update_volume(0)
                sel.update_select(0)
                mut.force_mute()
                dis.standby_screen()
                self.state = STATE_STANDBY

    def operate_to_bal(self, vol):
        vol.update_balance(0)
        self.state = STATE_BALANCE

    def bal_to_operate(self, vol):
        vol.update_volume(0)
        self.state = STATE_OPERATE

    def bal_to_tt_display(self, tim):
        tim.show_tt(0)
        self.state = STATE_TT_DISPLAY

    def goto_operate(self, vol, sel, mut, dis, tmp):
        dis.clear_display()
        dis.operate_on()
        vol.update_volume(0)
        dis.display_select(sel.get_current_select())
        mut.display_mute_state()
        tmp.update()
        self.state = STATE_OPERATE

    def tt_dis_to_bright(self, dis):
        dis.clear_display()
        dis.display_brightness()
        self.state = STATE_BRIGHTNESS
