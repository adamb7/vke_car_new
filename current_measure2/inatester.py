from ina233 import * #uj
import time
import os

if __name__== '__main__':
    StartLipoMonitorSampling()
    while True:
        print(data_readings["voltage"])
        print(data_readings["current"])
        print(data_readings["power"])
        print(get_readings())
        time.sleep(5)