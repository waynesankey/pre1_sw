from config import *


class Selector:
    def __init__(self, vol_obj, mus_obj, dis_obj, rel_obj):
        self.vol = vol_obj
        self.mus = mus_obj
        self.dis = dis_obj
        self.rel = rel_obj
        self.available_selects = self._load_available_selects()
        self.select = self.available_selects[0]
        self.on_select_changed = None

    def _load_available_selects(self):
        try:
            keys = sorted(int(k) for k in self.dis.selector_info.keys())
            keys = [k for k in keys if k >= SELECT_MIN]
            if keys:
                return keys
        except (AttributeError, ValueError, TypeError):
            pass
        return list(range(SELECT_MIN, SELECT_MIN + SELECT_COUNT))

    def _normalize_select(self, select_value):
        if select_value <= self.available_selects[0]:
            return self.available_selects[0]
        if select_value >= self.available_selects[-1]:
            return self.available_selects[-1]
        return select_value

    def update_select(self, select_change):
        print("Entering update_select,current select is %i and change is %i" % (self.select, select_change))
        if select_change == 0:
            self.select_immediate()
            return False
        select_old = self.select
        select_idx = self.available_selects.index(self.select)
        if select_change > 0:
            select_idx = min(select_idx + 1, len(self.available_selects) - 1)
        else:
            select_idx = max(select_idx - 1, 0)
        select_new = self.available_selects[select_idx]
        if select_new == select_old:
            return False
        self.select = select_new
        if self.on_select_changed is not None:
            try:
                self.on_select_changed()
            except Exception:
                pass

        print("In update_select, new select is", self.select)
        volume_left = self.vol.get_current_volume_left()
        volume_right = self.vol.get_current_volume_right()
        self.mus.vol_down_soft(volume_left, volume_right)
        self.dis.display_select(self.select)
        self.rel.select(self.select)
        self.mus.vol_up_soft(volume_left, volume_right)
        return True

    def apply_select(self, select_value):
        print("Entering apply_select, current select is %i and value is %i" % (self.select, select_value))
        select_old = self.select
        self.select = self._normalize_select(select_value)
        if self.select == select_old:
            return False
        if self.on_select_changed is not None:
            try:
                self.on_select_changed()
            except Exception:
                pass
        volume_left = self.vol.get_current_volume_left()
        volume_right = self.vol.get_current_volume_right()
        self.mus.vol_down_soft(volume_left, volume_right)
        self.dis.display_select(self.select)
        self.rel.select(self.select)
        self.mus.vol_up_soft(volume_left, volume_right)
        return True

    def select_immediate(self):
        self.dis.display_select(self.select)
        self.rel.select(self.select)

    def get_current_select(self):
        return self.select

    def set_select(self, select_value):
        self.select = self._normalize_select(select_value)

    def get_labels_line(self):
        labels = []
        for idx in self.available_selects:
            try:
                name = str(self.dis.selector_info[str(idx)])
            except (KeyError, ValueError, AttributeError):
                name = str(idx)
            safe_name = name.replace('"', "'")
            labels.append('INP%d="%s"' % (idx, safe_name))
        return "SELECTOR_LABELS " + " ".join(labels)
