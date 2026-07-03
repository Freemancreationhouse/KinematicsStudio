class MachineManager:

    def __init__(self):

        self.connected = False

        self.machine_name = None

    # --------------------------------

    def connect(self, name):

        self.machine_name = name

        self.connected = True

    # --------------------------------

    def disconnect(self):

        self.machine_name = None

        self.connected = False

    # --------------------------------

    @property
    def status(self):

        if self.connected:

            return f"Connected : {self.machine_name}"

        return "Disconnected"