import time
from urandom import getrandbits

from modules.tempsensor import TempSensor


class NoSensor(TempSensor):
    UPDATE_INTERVAL_MS = 10_000

    def __init__(self):
        super().__init__()
        self._last_update_ms = None
        self.update(force=True)

    def update(self, force=False):
        now = time.ticks_ms()
        if not force and self._last_update_ms is not None:
            if time.ticks_diff(now, self._last_update_ms) < self.UPDATE_INTERVAL_MS:
                return

        # Test mode when no physical sensor is present.
        # Produces a pseudo-temperature in 35..55 C with a marker suffix.
        self.temperature = str(35 + (getrandbits(8) % 21)) + "*"
        self._last_update_ms = now
