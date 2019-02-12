import time
import threading
from IRSensor import IRSensor as ir

address = 0x48
data = 0
bus = ir.bus
current_sampling_rate = 5


def read(chn=0): #channel
	global address,bus
	try:
		if chn == 0:
			bus.write_byte(address,0x40)
		if chn == 1:
			bus.write_byte(address,0x41)
		if chn == 2:
			bus.write_byte(address,0x42)
		if chn == 3:
			bus.write_byte(address,0x43)
		bus.read_byte(address) # dummy read to start conversion
	except Exception, e:
		print "Address: %s" % address
		print e

	return bus.read_byte(address)

def StartCurrentSampling():
    k = threading.Thread(target=read_loop,name="current_reader")
    k.setDaemon(True)
    k.start()

def calculate_current(current_data):
	data_out = ((3300 *current_data) /256) #miliamps
	return data_out

def read_current():
    return data

def read_loop():
	global data
	global current_sampling_rate
	while True:
		temp = read(3)
		data = calculate_current(temp)
		time.sleep(current_sampling_rate)

'''
if __name__ == "__main__":
	StartCurrentSampling()
	try:
		while True:
			a = read_current()
			print(a)
			time.sleep(1)
	except KeyboardInterrupt:
		print("end")
'''

'''
class CurrentMeasure:
    TIME_DELAY = 30
    CHANNEL = 3         #A0
    TOPIC_NAME = "current"
    ADDRESS = 0x48

    def __init__(self):
        #Thread.__init__(self)
        self._delay     =   self.TIME_DELAY
        self._channel   =   self.CHANNEL
        self._topic     =   self.TOPIC_NAME
        self._bus       =   smbus.SMBus(1)

    def current_check(self):
        data = self._bus.read_byte(self.ADDRESS)
        print(data)
        time.sleep(self.TIME_DELAY)

'''
'''
if __name__ == "__main__":
    #curr = CurrentMeasure()
    #curr.run()
    bus = smbus.SMBus(1)
    bus.write_byte(0x48,0x00)
    while True:
        data = bus.read_byte(0x48)
        print(data)
        time.sleep(10)
'''

'''
#car_main
ir.StartCurrent()#ir.StartSampling utan!

def publish_current():
    while True:
        data = ir.read(3)
        client.publish("current", data)
        time.sleep(10)

def StartCurrent():
    k = threading.Thread(target=publish_current)
    k.setDaemon(True)
    k.start()


#IRCONFIG eleje
eventBlock = threading.Event()
#IRCONFIG READ FV
eventBlock.wait()
eventBlock.clear()
#...
#...
eventBlock.set()

'''

# sampling / IsobstaclePresent -> checkvalues -> read
# global valtozoba mentunk, checkvaluesba olvas
# current_read olvassa
# kulon szal publisholja




'''
IRconfig:
read fv => blokkolo kell!!!!

car_main:
1)fv def
while true:
    olvas (ir.read?)
    wait 30 sec
publish

2)threading.start (daemon!)

'''