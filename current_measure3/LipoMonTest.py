from LipoMonitor import LipoMonitor as lipo
from car_main import client
from car_main import flag_connect
import time


if __name__ == '__main__':
    lipo.StartLipoMonitorSampling()
    while True:
        data = lipo.get_readings()
        print(lipo.get_readings())
        if flag_connect:
            client.publish("current", data["current"])
            client.publish("voltage", data["voltage"])
            client.publish("power", data["power"])
        time.sleep(5)
