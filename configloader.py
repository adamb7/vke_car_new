import json
import ledcontrol

class ConfigLoader():

	def __init__(self,fname): # thorws: FileExceptions and JSON parse exceptions

		with open(fname) as f:
			self._conf = json.load(f)

		if not self._checkConfig():
			raise Exception("Bad config")

	def _checkConfig(self):
		keys_to_check = ['ledconfig','led_inverted','rgb_led','forward_speed','ir_sensitivity']

		for k in keys_to_check:
			if not k in self._conf:
				return False

		return True

	def getLedconfig(self):
		return self._conf['ledconfig']

	def getLedInversion(self):
		return self._conf['led_inverted']

	def getResetAnimation(self):

		if self._conf['rgb_led']:
			return ledcontrol.LEDAnimationBlue()
		else:
			return ledcontrol.LEDAnimationSwitching()

	def getForwardSpeed(self):
		return self._conf['forward_speed']

	def getIRSensitivity(self):
		return self._conf['ir_sensitivity']
