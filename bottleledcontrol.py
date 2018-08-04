#!/usr/bin/env python2
import neopixel
from threading import Thread,Event,RLock
import time

class BottleLedControl(Thread):

	LED_COUNT      = 7
	LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
	LED_DMA        = 9      # DMA channel to use for generating signal (default 10)
	# DMA channels to be avoided: 1,3,6,7 = used by GPU, 0 = used by frame buffer, 2 = used by SD card
	LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
	LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

	ANIMATION_FILL 		= 1
	ANIMATION_EMPTY 	= 2
	ANIMATION_WIPE 		= 3
	ANIMATION_DEFAULT 	= 4
	ANIMATION_OFF		= 5

	COLOR_BEER = neopixel.Color(165, 42, 0)
	COLOR_OFF  = neopixel.Color(0, 0, 0)
	COLOR_RED  = neopixel.Color(255, 0, 0)


	def __init__(self,pin,default_anim,brightness=255):

		Thread.__init__(self)

		self._strip = neopixel.Adafruit_NeoPixel(self.LED_COUNT, pin, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, brightness, self.LED_CHANNEL)

		self._animation = default_anim
		self._new_animation_event = Event()
		self._running = True

		self._pause_event = Event()
		self._pause_event.set()

		self._locker = RLock()

		# dunno better
		self._bottle_fill_level = 0 # liquid szint
		self._wipe_pointer = 0 # meddig lett letorolve


	# set all leds, not just the ones that are changed, used to clean up animation
	def _fillPartition(self,first,last,color): # first and last led are inclusive

		for i in range(self.LED_COUNT):

			if i >= first and i <= last: # in the range

				self._strip.setPixelColor(i,color)
			else: # outside range
				self._strip.setPixelColor(i,self.COLOR_OFF)


	def run(self):
		self._strip.begin()

		while self._running:

			self._pause_event.wait() # wait if paused

			if self._animation:

				delay = 0 # azert, hogy a locking oda kerulhessen ahol van

				with self._locker: # ez nagyon csunya lesz... de nem akartam kifutni a hataridobol

					if self._animation == self.ANIMATION_FILL: # fills up bottles
						self._wipe_pointer = 0

#						self._fillPartition(0,self._bottle_fill_level,self.COLOR_BEER) # we use this, so unclean animation switch (animation not finished before changed to another) won't cause problems # debug miatt ki lett kommentezve, elv jonak kellene lennie, de valamiert neha elofordul, hogy kettesevel, vagy haramsaval kapcsolnak fel a ledek, mintha egy-ket ciklusra kimaradnak a .show() hivas
						self._strip.setPixelColor(self._bottle_fill_level,self.COLOR_BEER) # ez kevesebb ledet allit egyszerre, talan nem jon elo a problema

						if self._bottle_fill_level == (self.LED_COUNT-1):
							self._animation = None
						else:
							self._bottle_fill_level += 1

						delay = 0.83 # ez ki van szamolva keremszepen


					elif self._animation == self.ANIMATION_EMPTY: # empty bottles
						self._wipe_pointer = 0

						self._fillPartition(0,self._bottle_fill_level,self.COLOR_BEER)

						if self._bottle_fill_level == 0:
							self._animation = self.ANIMATION_DEFAULT
						else:
							self._bottle_fill_level -= 1

						delay = 0.2


					elif self._animation == self.ANIMATION_WIPE:
						self._bottle_fill_level = 0

						self._strip.setPixelColor(self._wipe_pointer,self.COLOR_OFF)

						if self._wipe_pointer == (self.LED_COUNT-1):

							self._wipe_pointer = 0
							self._animation = self.ANIMATION_OFF

						else:
							self._wipe_pointer += 1

						delay = 0.05

					elif self._animation == self.ANIMATION_DEFAULT: # turns off all leds, and the first one to red, then stops the animator
						self._bottle_fill_level = 0
						self._wipe_pointer = 0


						self._fillPartition(0,0,self.COLOR_RED)


						self._animation = None



					elif self._animation == self.ANIMATION_OFF: # turns off all leds, then stops the animator
						self._bottle_fill_level = 0
						self._wipe_pointer = 0

						for i in range(0,self.LED_COUNT):
							self._strip.setPixelColor(i,self.COLOR_OFF)

						self._animation = None


					else: # undefinied animation
						self._animation = None


				# thing is.... neopixel library is not good
				for i in range(5): # so we patch it around here; all this does is calling show 5 times, so a broken show may be fixed by the other 4
					self._strip.show()
					time.sleep(delay/5)
				self._strip.show() # +1


			else:
				self._new_animation_event.wait() # wait for an animation to load
				self._new_animation_event.clear()


	def _setAnimation(self,anim): # this part actually does not require locking because....
		self._animation = anim # this is atomic
		self._new_animation_event.set() # this is thread safe (obviously)

	def getAnimation(self):
		return self._animation # atomic			

	def startFill(self,reset=True,autoUnpause=True): # fill up bottles
		with self._locker:
			self._setAnimation(self.ANIMATION_FILL)
			if reset:
				self._bottle_fill_level = 0

			if autoUnpause:
				self.resume()

	def startEmpty(self,reset=True,autoUnpause=True): # empty out bottles
		with self._locker:
			self._setAnimation(self.ANIMATION_EMPTY)
			if reset:
				self._bottle_fill_level = self.LED_COUNT-1

			if autoUnpause:
				self.resume()

	def startWipe(self,reset=True,autoUnpause=True): # wipe up all the colors
		with self._locker:
			self._setAnimation(self.ANIMATION_WIPE)
			if reset:
				self._wipe_pointer = 0

			if autoUnpause:
				self.resume()

	def setDefault(self,autoUnpause=True): # turns off all leds except the first one which turns red
		with self._locker:
			self._setAnimation(self.ANIMATION_DEFAULT)

			if autoUnpause:
				self.resume()


	def setOff(self,autoUnpause=True): # turns off all leds
		with self._locker:
			self._setAnimation(self.ANIMATION_OFF)

			if autoUnpause:
				self.resume()


	def pause(self):
		self._pause_event.clear()

	def resume(self):
		self._pause_event.set()

	def shutdown(self):
		self._running = False
		self._new_animation_event.set() # so that it can exit
		self._pause_event.set()


