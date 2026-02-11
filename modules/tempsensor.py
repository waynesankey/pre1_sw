class TempSensor:
    def __init__(self):
        self.temperature = None

    def update(self):
        raise NotImplementedError("TempSensor.update() must be implemented by subclasses")
