from modules.tempsensor import TempSensor


class NoSensor(TempSensor):
    def __init__(self):
        super().__init__()

    def update(self):
        return
