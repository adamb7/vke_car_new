#!/usr/bin/env python2
from LipoMonitor import LipoMonitor as lipo
import os
import time
import paho.mqtt.client as mqtt
import traceback
import logging


flag_connect = 0  #uj

mqtt_username = "user"
mqtt_password = "user"
mqtt_broker_ip = "10.3.141.3"
mqtt_broker_port = 1883
client = mqtt.Client()

def init_mqtt():
    global client
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    return MQTTReconnect()

def MQTTReconnect():  # mostantol ez vegtelenszer probalkozik
    reconn_counter = 0
    while True:
        try:
            print("lipo Kapcsolodasi kiserlet...")
            client.connect(mqtt_broker_ip, mqtt_broker_port)
            return True

        except KeyboardInterrupt:
            raise  # ezt tovabb dobjuk, hogy le tudjon allni a progi

        except:
            print("lipo: A kapcsolodas nem sikerult az mqtt brokerhez (%i), ujraprobalas..." % reconn_counter)
            reconn_counter += 1
            time.sleep(5)

def on_connect(client, userdata, flag, rc):
    global flag_connect  #uj
    print("Lipo MQTT Connected!", str(rc))
    flag_connect = 1  #uj

def on_message(client, userdata, msg):
    global stop_active, reset_active, pause_event
    global shutdown_timer  # ez rosszabb

def on_publish(client, userdata, mid):
    print("lipo Message published: " + str(mid))

def on_disconnect(client, userdata, result):
    global flag_connect  #uj
    flag_connect = 0  #uj
    if result != 0:
        # logolas!
        print("LIPO: A kocsi es broker kozti kommunikacio megszakadt.")

        if (not MQTTReconnect()):
            print("LIPO: A kapcsolodas nem sikerult, az alkalmazas leall...")
            # alkalmazast kikapcsolni
            return
        else:
            print("LIPO: A visszakapcsolodas sikerult.")
            return

def main():
    global client
    lipo.StartLipoMonitorSampling()
    while True:
        data = lipo.get_readings()
        if data["voltage"] < 6.5:
            print("Battery is low! Attempting to shutdown system...")
            lipo.shutdown_car()
        if flag_connect:
            client.publish("current", data["current"])
            client.publish("voltage", data["voltage"])
            client.publish("power", data["power"])
            client.publish("shunt", data["shunt"])
        else:
            print("lipo no connect")
        time.sleep(5)


if __name__ == '__main__':
    try:
        if init_mqtt():
            client.loop_start()
            main()
        else:
            print
            "lipo A kapcsolodas nem sikerult az mqtt brokerhez"

    except KeyboardInterrupt:
        print("Keyboard Interrupt")

    except SystemExit:
        os._exit(0)

    except:
        logging.debug(traceback.print_exc())

    finally:
        client.disconnect()
