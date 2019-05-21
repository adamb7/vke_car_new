#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import time
import threading
import os
from IRSensor import IRSensor as ir

MAX_CURRENT     = 5.0  # 5 AMPER
R_SHUNT         = 0.1  # 100 mOHM
CURRENT_LSB = MAX_CURRENT / 32768.0
CAL = int(round((5.12 / (CURRENT_LSB * R_SHUNT)) / 1000))  # CAL = 335
#CAL = 336
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

init_flag = 0  # for shutdown
address = 0x45  # A0,A1: VCC
bus = ir.bus
monitor_sampling_rate = 5
data_readings = {
    "current": 0,
    "voltage": 8,
    "power"	:	0,
    "shunt":   0,
    "car_power": 0
}



def init_ina233():
    global address, init_flag
    try:
        bus.write_byte(address, CLEAR_FAULTS)
	bus.write_word_data(address,MFR_CALIBRATION,CAL)
	if bus.read_word_data(address,MFR_CALIBRATION) != CAL:
		init_flag = 0
	else:	
		init_flag = 1
    except Exception, e:
        print "Lipo monitor init failed"
        print "Address: %s" % address
        print e
        init_flag = 0

def read_current():
    global address, bus
    try:
        current_data = bus.read_word_data(address, READ_IN)
    except Exception, e:
        print "Current read error"
        print "Address: %s" % address
        print e
    return current_data

def read_voltage():
    global address, bus
    try:
        voltage_data = bus.read_word_data(address, READ_VIN)
    except Exception, e:
        print "Voltage read error"
        print "Address: %s" % address
        print e
    return voltage_data

def read_power():
    global address, bus
    try:
        power_data = bus.read_word_data(address, READ_PIN)
    except Exception, e:
        print "Power read error"
        print "Address: %s" % address
        print e
    return power_data

def read_shunt():
    global address, bus
    try:
        shunt_data = bus.read_word_data(address, MFR_READ_VSHUNT)
    except Exception, e:
        print "Shunt voltage read error"
        print "Address: %s" % address
        print e
    return shunt_data

def calculate_measurement(source):
    global CURRENT_LSB
    r = 0
    b = 0.0
    try:
        if (source != "voltage") & (source != "shunt") :
            if source == "current":     # source = current
                m = 1.0 / CURRENT_LSB
                y = read_current()
            else:                       # source = power
                m = 1.0 / (25.0 * CURRENT_LSB)
                y = read_power()
            while m < 32768.0:
                m *= 10.0
                r += 1
            while m > 32768.0:
                m /= 10.0
                r -= 1
        else:                           # source = voltage
            if source == "voltage":
                m = 8  # 1.25 mV/bit
                r = 2
                y = read_voltage()
            else:                       # source = shunt
                m = 4  # 2.5 uV/bit
                r = 5
                y = read_shunt()
        x = (1.0 / m) * ((y * (pow(10, -r))) - b)
        return x
    except Exception, e:
        print "Conversion error"
        print e

def lipo_read_loop():
    global data_readings
    global monitor_sampling_rate
    global init_flag 
    init_ina233()
    while init_flag == 0:
	init_ina233()
    avg_voltage = 0
    read_trigger = 0
    #first read
    data_readings["current"] = calculate_measurement("current")
    data_readings["voltage"] = calculate_measurement("voltage")
    data_readings["power"] = calculate_measurement("power")
    #data_readings["shunt"] = calculate_measurement("shunt")
    data_readings["car_power"] = data_readings["current"] * data_readings["voltage"]
    while True:
        if read_trigger == monitor_sampling_rate:
            avg_voltage /= monitor_sampling_rate
            data_readings["current"] = calculate_measurement("current")
            data_readings["voltage"] = avg_voltage
            data_readings["power"] 	 = calculate_measurement("power")
            #data_readings["shunt"]   = calculate_measurement("shunt")
            data_readings["car_power"] = data_readings["current"] * data_readings["voltage"]
            avg_voltage = 0
            read_trigger = 0
        avg_voltage  += calculate_measurement("voltage")
        read_trigger += 1
        time.sleep(1)

def StartLipoMonitorSampling():
    k = threading.Thread(target=lipo_read_loop)
    k.setDaemon(True)
    k.start()

def get_readings():
    return data_readings

def shutdown_car():
    global init_flag
    if init_flag:
        print("Shutting down car...")
        os.system('systemctl poweroff')

# def value_avg():
#     global avg_voltage
#     try:
#         avg = 0
#         for i in xrange(5):
#             value = calculate_measurement("voltage")
#             avg += value
#             time.sleep(1)
#         avg_voltage = avg / 5
#     except Exception, e:
#         print("Voltage sampling failed")
#         print(e)

# #"""FOR TESTING"""
# if __name__ == '__main__':
#     try:
#         #init_ina233()
#         print(CAL)
#         # print("Voltage in V:")
#         # print(calculate_measurement("voltage"))
#         # print("Current in A:")
#         # print(calculate_measurement("current"))
#         # print("Power in W:")
#         # print(calculate_measurement("power"))
#     except Exception, e:
#         print "Test failed"
#         print e
