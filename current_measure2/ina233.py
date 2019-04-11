# -*- coding: utf-8 -*-
from __future__ import division
import time
import threading
from IRSensor import IRSensor as ir
#from ina233commands import *
#__import__("ina233commands")

MAX_CURRENT     = 5  # 5 AMPER
R_SHUNT         = 0.1  # 100 mOHM
CURRENT_LSB     = MAX_CURRENT / 32768
#CAL = int(round(0.00512 / (CURRENT_LSB * R_SHUNT)))
CAL = 337
#CAL_HEX = hex(int(round(CAL))) #####
CLEAR_FAULTS 		    = 0x03
RESTORE_DEFAULT_ALL 	= 0x12
CAPABILITY 		        = 0x19
IOUT_OC_WARN_LIMIT	    = 0x4A
VIN_OV_WARN_LIMIT	    = 0x57
VIN_UV_WARN_LIMIT	    = 0x58
PIN_OP_WARN_LIMIT	    = 0x6B
STATUS_BYTE		        = 0x7B
STATUS_WORD		        = 0x79
STATUS_IOUT		        = 0x7B
STATUS_INPUT		    = 0x7C
STATUS_CML		        = 0x7E
STATUS_MFR_SPECIFIC	    = 0x80
READ_EIN		        = 0x86
READ_VIN		        = 0x88
READ_IN			        = 0x89
READ_VOUT		        = 0x8B
READ_IOUT		        = 0x8C
READ_POUT		        = 0x96
READ_PIN		        = 0x97
MFR_ID			        = 0x99
MFR_MODEL		        = 0x9A
MFR_REVISION		    = 0x9B
MFR_ADC_CONFIG		    = 0xD0
MFR_READ_VSHUNT		    = 0xD1
MFR_ALERT_MASK		    = 0xD2
MFR_CALIBRATION		    = 0xD4
MFR_DEVICE_CONFIG	    = 0xD5
CLEAR_EIN		        = 0xD6
TI_MFR_ID		        = 0xE0
TI_MFR_MODEL		    = 0xE1
TI_MFR_REVISION         = 0xE2

address = 0x45  # A0,A1: VS
bus = ir.bus
monitor_sampling_rate = 5
data_readings = {
    "current": 0,
    "voltage": 0,
    "power"	:	0
}



def init_ina233():
    global address, CAL_HEX
    try:
        bus.write_byte(address, CLEAR_FAULTS)
        bus.write_word_data(address,MFR_CALIBRATION, CAL)

    except Exception, e:
        print "Lipo monitor init failed"
        print "Address: %s" % address
        print e

def read_current():
    global address ,bus
    try:
        current_data = bus.read_word_data(address, READ_IN)
    except Exception, e:
        print "Current read error"
        print "Address: %s" % address
        print e
    return current_data

def read_voltage():
    global address ,bus
    try:
        voltage_data = bus.read_word_data(address, READ_VIN)
    except Exception, e:
        print "Voltage read error"
        print "Address: %s" % address
        print e
    return voltage_data

def read_power():
    global address ,bus
    try:
        power_data = bus.read_word_data(address, READ_PIN)
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
            if source == "current":     # source = current
                m = 1 / CURRENT_LSB
                Y = read_current()
            else:                       # source = power
                m = 1 / (25 *CURRENT_LSB)
                Y = read_power()
            while m < 32768:
                m *= 10
                R += 1
            while m > 32768:
                m /= 10
                R -= 1
        else:                           # source = voltage
            m = 8  # 1.25 mV/bit
            R = 2
            Y = read_voltage()
        X = (1 / m) * ((Y * (pow(10,-R)))  - b)
        return X
    except Exception, e:
        print "Conversion error"
        print e

def read_loop():
    global data_readings
    global monitor_sampling_rate
    init_ina233()
    while True:
        data_readings["current"] = calculate_measurement("current")
        data_readings["voltage"] = calculate_measurement("voltage")
        data_readings["power"] 	 = calculate_measurement("power")
        time.sleep(monitor_sampling_rate)


# def StartCurrentSampling(): #main: change!
def StartLipoMonitorSampling():
    k = threading.Thread(target=read_loop ,name="lipomonitor")
    k.setDaemon(True)
    k.start()

def get_readings():
    return data_readings

# #"""FOR TESTING"""
# if __name__ == '__main__':
#     try:
#         init_ina233()
#         print("Voltage in V:")
#         print(calculate_measurement("voltage"))
#         print("Current in A:")
#         print(calculate_measurement("current"))
#         print("Power in W:")
#         print(calculate_measurement("power"))
#     except Exception, e:
#         print "Test failed"
#         print e


# """lipo_monitor.py: INA233IDGST handling functions
#
# Calibration register values were calculated with following method:
# 	Current_LSB 	= MAX_CURRENT / 32768
# 	CAL 		= 0.00512 / (Current_LSB * RShunt)
# 	MAX_CURRENT 	= 5
# 	R_SHUNT 	= 0.1
# 	Current_LSB 	= 152 * 10-6 #higher LSB => smaller rounding error
# 	CAL 		= 336.8421 (337) ===> 0x151
# Reconversion of received data: Y -> X
# The value of 0 can be used for b for both current and power measurements with very little loss in accuracy
# because the offset for power and current measurements is very low.
# 	b = 0
# The voltage LSB for bus voltage and shunt voltage are fixed at 1.25 mV/bit and 2.5 µV/bit.
# 	m = 8
# 	R = 2
# 	X = (1 / m) * (Y * 10^[-R]  - b)
# Calculating m,R for current measurement:
# 	m = 1 / Current_LSB
# 	m : move decimal point to maximize value, but stay in [-32767,32767] interval
# 	#this minimizes rounding errors!
# 	if *10 => R = -1 	(m shifted right)
# 	if /10 => R = 1 	(m shifted left)
# Calculating m,R for power measurement:
# 	m = 1 / (25 * Current_LSB)
# 	rest is same as with current!
# 	X = (1 / m) * (Y * 10^[-R]  - b)
# """