"""
Safety controller: bounds checking and watchdog for PFAL simulation.
Clamps all control variables to safe setpoints and can trigger emergency actions if instability is detected.
"""

class SafetyController:
    def __init__(self, safe_bounds):
        """
        safe_bounds: dict of {var: (min, max)}
        """
        self.safe_bounds = safe_bounds
        self.last_values = {}
        self.unstable = False

    def check(self, values):
        """
        values: dict of {var: value}
        Returns: (clamped_values, emergency)
        """
        clamped = {}
        emergency = False
        for var, val in values.items():
            if var in self.safe_bounds:
                lo, hi = self.safe_bounds[var]
                if val < lo or val > hi:
                    emergency = True
                    clamped[var] = max(lo, min(val, hi))
                else:
                    clamped[var] = val
            else:
                clamped[var] = val
        self.last_values = clamped
        self.unstable = emergency
        return clamped, emergency

    def is_unstable(self):
        return self.unstable
