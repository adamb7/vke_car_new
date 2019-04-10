# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""lipo_monitor.py: INA233IDGST handling functions

Calibration register values were calculated with following method:
	Current_LSB 	= MAX_CURRENT / 32768
	CAL 		= 0.00512 / (Current_LSB * RShunt)
	MAX_CURRENT 	= 5
	R_SHUNT 	= 0.1
	Current_LSB 	= 152 * 10-6 #higher LSB => smaller rounding error
	CAL 		= 336.8421 (337) ===> 0x151
Reconversion of received data: Y -> X
The value of 0 can be used for b for both current and power measurements with very little loss in accuracy
because the offset for power and current measurements is very low.
	b = 0
The voltage LSB for bus voltage and shunt voltage are fixed at 1.25 mV/bit and 2.5 µV/bit.
	m = 8
	R = 2
	X = (1 / m) * (Y * 10^[-R]  - b)
Calculating m,R for current measurement:
	m = 1 / Current_LSB
	m : move decimal point to maximize value, but stay in [-32767,32767] interval
	#this minimizes rounding errors!
	if *10 => R = -1 	(m shifted right)
	if /10 => R = 1 	(m shifted left)
Calculating m,R for power measurement:
	m = 1 / (25 * Current_LSB)
	rest is same as with current!
	X = (1 / m) * (Y * 10^[-R]  - b)
"""


import sys
import time
import threading

from IRSensor import IRSensor as ir
from ina233 import *

__import__("ina233")

MAX_CURRENT = 5  # 5 AMPER
R_SHUNT = 0.1  # 100 mOHM
CURRENT_LSB = MAX_CURRENT / 32768
#CAL = 0.00512 / (CURRENT_LSB * R_SHUNT)
CAL = 337
CAL_HEX = hex(int(round(CAL)))

address = 0x45  # A0,A1: VS
bus = ir.bus
sampling_rate = 5
data_readings = {
    "current": 0,
    "voltage": 0,
    "power"	:	0
}



def init_ina233():
    global address, CAL_HEX
    try:
        val = CAL_HEX  # calculated CAL value
        #bus.write_i2c_block_data(address ,CLEAR_FAULTS, 1)
        bus.write_i2c_block_data(address, 0, [MFR_CALIBRATION,  0x151])
        #voltage_data = bus.read_i2c_block_data(address, READ_VIN, 2)
        #print(hex(int(voltage_data[0])))
        #print(hex(int(voltage_data[1])))
        #bus.write_byte_data(address, 0, MFR_CALIBRATION)
        #bus.write_byte_data(address, 0, 0x151)

    except Exception, e:
        print "Lipo monitor init failed"
        print "Address: %s" % address
        print e

def read_current():
    global address ,bus
    try:
        current_data = bus.read_i2c_block_data(address ,READ_IN ,2)
    except Exception, e:
        print "Current read error"
        print "Address: %s" % address
        print e
    return current_data

def read_voltage():
    global address ,bus
    try:
        voltage_data = bus.read_i2c_block_data(address ,READ_VIN ,2)
    except Exception, e:
        print "Voltage read error"
        print "Address: %s" % address
        print e
    return voltage_data

def read_power():
    global address ,bus
    try:
        power_data = bus.read_i2c_block_data(address ,READ_PIN ,2)
    except Exception, e:
        print "Power read error"
        print "Address: %s" % address
        print e
    return power_data

def calculate_measurement(source):
    global CURRENT_LSB
    R 		= 0
    b 		= 0
    try:
        if source != "voltage":
            if source == "current":  # source = current
                m = 1 / CURRENT_LSB
                Y = read_current()
            else:  # source = power
                m = 1 / (25 *CURRENT_LSB)
                Y = read_power()
            while m < 32768:
                m *= 10
                R += 1
            while m > 32768:
                m /= 10
                R -= 1
        else:  # source = voltage
            m = 8  # 1.25 mV/bit
            R = 2
            Y = read_voltage()
        X = (1 / m) * ((Y * (10 ^(-R)))  - b)
        return X
    except Exception, e:
        print "Conversion error"
        print e

def read_loop():
    global data_readings
    global sampling_rate
    init_ina233()
    while True:
        data_readings["current"] = calculate_measurement(current)
        data_readings["voltage"] = calculate_measurement(voltage)
        data_readings["power"] 	 = calculate_measurement(power)
        time.sleep(sampling_rate)


# def StartCurrentSampling(): #main: change!
def StartLipoMonitorSampling():
    k = threading.Thread(target=read_loop ,name="ina233_reader")
    k.setDaemon(True)
    k.start()

def get_readings():
    return data_readings

"""FOR TESTING"""
if __name__ == '__main__':
    try:
        init_ina233()
        #print(read_current)
        #print(read_voltage)
        #print(read_power)

    except Exception, e:
        print "Test failed"
        print e
