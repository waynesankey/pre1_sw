class Encoder_25LB22_Q:
    def __init__(self, pin_a, pin_b):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.current = self.pin_a.value() << 1 | self.pin_b.value()
        self.last = self.current

    def change(self):
        knob_change = 0
        self.current = self.pin_a.value() << 1 | self.pin_b.value()
        if self.current != self.last:
            if self.last == 3 and self.current == 1:
                knob_change = 1
            elif self.last == 3 and self.current == 2:
                knob_change = -1
            self.last = self.current
        return knob_change
