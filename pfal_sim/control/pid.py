
"""
VPD control using PID on (T, RH) to drive HVAC/dehumidifier to a VPD setpoint.
Setpoint can be varied by crop stage.
"""
import math

class PID:
	def __init__(self, Kp, Ki, Kd, setpoint, output_limits=(None, None)):
		self.Kp = Kp
		self.Ki = Ki
		self.Kd = Kd
		self.setpoint = setpoint
		self.output_limits = output_limits
		self._last_error = 0.0
		self._integral = 0.0
		self._last_value = None

	def step(self, value, dt):
		error = self.setpoint - value
		self._integral += error * dt
		derivative = 0.0
		if self._last_value is not None:
			derivative = (error - self._last_error) / dt
		output = self.Kp * error + self.Ki * self._integral + self.Kd * derivative
		# Clamp output
		low, high = self.output_limits
		if low is not None:
			output = max(low, output)
		if high is not None:
			output = min(high, output)
		self._last_error = error
		self._last_value = value
		return output

def vpd(T, RH):
	"""
	Calculate VPD (kPa) from temperature (C) and relative humidity (0-1).
	"""
	# Saturation vapor pressure (kPa)
	es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))
	ea = RH * es
	return max(0.0, es - ea)

class VPDController:
	def __init__(self, vpd_setpoint, Kp=1.0, Ki=0.0, Kd=0.0, output_limits=(-1, 1)):
		self.pid = PID(Kp, Ki, Kd, vpd_setpoint, output_limits)
		self.vpd_setpoint = vpd_setpoint

	def step(self, T, RH, dt):
		current_vpd = vpd(T, RH)
		control_signal = self.pid.step(current_vpd, dt)
		# control_signal < 0: humidify, > 0: dehumidify/cool
		return control_signal, current_vpd

