"""
CO2 controller for on-light hours with ppm setpoint, hard ceiling, and lockout if door is open.
"""

class CO2Controller:
    def __init__(self, setpoint_ppm, hard_ceiling_ppm, door_open_lockout=True):
        self.setpoint_ppm = setpoint_ppm
        self.hard_ceiling_ppm = hard_ceiling_ppm
        self.door_open_lockout = door_open_lockout
        self.injecting = False

    def step(self, current_ppm, lights_on, door_open):
        """
        Decide whether to inject CO2 based on current state.
        Returns: 'INJECT_ON', 'INJECT_OFF', or 'LOCKOUT'
        """
        if self.door_open_lockout and door_open:
            self.injecting = False
            return 'LOCKOUT'
        if not lights_on:
            self.injecting = False
            return 'INJECT_OFF'
        if current_ppm >= self.hard_ceiling_ppm:
            self.injecting = False
            return 'INJECT_OFF'
        if current_ppm < self.setpoint_ppm:
            self.injecting = True
            return 'INJECT_ON'
        self.injecting = False
        return 'INJECT_OFF'
