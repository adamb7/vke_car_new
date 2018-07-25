#!/usr/bin/env python2

from SunFounder_Line_Follower import Line_Follower
from picar import front_wheels
from picar import back_wheels
import time
import os
import picar
import datetime
import threading
import paho.mqtt.client as mqtt
import traceback
import logging
from IRSensor import IRSensor as ir

from RPi import GPIO
import ledcontrol
from bottleledcontrol import BottleLedControl
import configloader

# first

carconfig = configloader.ConfigLoader("/etc/carconfig.json") # any exception this function throws should kill the program

#init / setup metodusba
GPIO.setmode(GPIO.BCM)

lc = ledcontrol.LEDControl(carconfig.getLedconfig(), ledcontrol.LEDAnimationGood(), carconfig.getLedInversion()) # inicializaljuk a ledvezerlot a car descriptionnak megfeleloen
lc.start()

blc = BottleLedControl(12,BottleLedControl.ANIMATION_OFF)
blc.start()


carManagement = "carManagement"

stop_active = True
reset_active = False # csak arra van hasznalva, hogy skippelje a vonalakat

pause_event = threading.Event() # magyarazat: lasd. gateway
pause_event.set() # not blocking by default; True = not paused, False = paused

picar.setup()

#REFERENCES = [270,290,300,290,270]
REFERENCES = [330,330,330,330,330]
refFile = "../referenceConfig"

fw = front_wheels.Front_Wheels(db='../wheel_config')
#fw.debug = True

bw = back_wheels.Back_Wheels(db='../wheel_config')
forwardSpeed = carconfig.getForwardSpeed()

lf = Line_Follower.Line_Follower()


fw.ready()
bw.ready()
#45
fw.turning_max = 50



logging.basicConfig(filename='car.log', level=logging.DEBUG, \
                    format="%(asctime)s %(message)s:")
logging.info("log started")


'''
IRSensing
'''
ir.maxValue = carconfig.getIRSensitivity() # change threshold value
obstacleErrorTime = 10
obstacle = False
#obstacleSeen = time.time()
def IRCallback():  
    global obstacleSeen, obstacle
    global client
    
    print("!!!!!!!!!!!!!!!!!!!!!!!!valamit latott!!!!!!!!!!!!!!!!!!!!!!!")
    if not obstacle:
        print("elindul az obstacle hiba")
        obstacle = True
        client.publish("forklift_obstacle_error")
        time.sleep(obstacleErrorTime)

        pause_event.wait() # ha pause volt, akkor megvarjuk amig az feloldodik

        while ir.IsObstaclePresent():
            time.sleep(0.125)
        
        obstacle = False
        client.publish("forklift_obstacle_error_reset")
            

ir.callback = IRCallback
ir.StartSampling()

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
    

def MQTTReconnect(): # mostantol ez vegtelenszer probalkozik
    
    reconn_counter = 0
    while True:
        try:
            print("Kapcsolodasi kiserlet...")
            client.connect(mqtt_broker_ip, mqtt_broker_port)
            return True
        
	except KeyboardInterrupt:
            raise # ezt tovabb dobjuk, hogy le tudjon allni a progi

        except:
            print("A kapcsolodas nem sikerult az mqtt brokerhez (%i), ujraprobalas..." % reconn_counter)
            reconn_counter += 1
            time.sleep(5)
        
def setup():
    try:
        with open(refFile) as file:
            content = file.readlines()
            content = [x.strip() for x in content]
            content = content[len(content) - 1].split(' ')
            content = [int(x) for x in content]

            #lf.references = content
            lf.references = REFERENCES
            #print(content)
            #print(REFERENCES)
            #print(lf.references)

    except:
        print "Beolvasi hiba tortent, manualis beallitas hasznalata..."
        logging.warning("Beolvasi hiba tortent, manualis beallitas hasznalata...")
        
        lf.references = REFERENCES
        
        traceback.print_exc()

def main():
    global stop_active,reset_active
    global stopped,pause_event

    a_step = 5  #3
    b_step = 15  #10
    c_step = 35  #30
    d_step = 45  #45

    last_time = time.time() # kezdeti erteket adunk neki, ezt arra hasznaljuk, hogy ket vonal triggerelt megallas kozott minimum 5mp teljen el

    while True:
        try:
            
            turning_angle = None # ezt en raktam ide -- Marci
            
            if (stop_active or obstacle or (not pause_event.isSet())): # pause event = False - paused; True - unpaused
                bw.stop()

            elif (not (stop_active or obstacle)) and pause_event.isSet():
                

                lt_status_now = lf.read_digital()
                #print(lt_status_now)
                #print(lf.read_analog())

                bw.speed = forwardSpeed
                bw.forward()
                
                step = 0 # ezt en raktam ide -- Marci

                # Angle calculate
                if lt_status_now == [0, 0, 1, 0, 0]:
                    step = 0
                    
                elif lt_status_now == [0, 1, 1, 0, 0] or lt_status_now == [0, 0, 1, 1, 0]:
                    step = a_step
                    
                elif lt_status_now == [0, 1, 0, 0, 0] or lt_status_now == [0, 0, 0, 1, 0]:
                    step = b_step
                    
                elif lt_status_now == [1, 1, 0, 0, 0] or lt_status_now == [0, 0, 0, 1, 1]:
                    step = c_step
                    
                elif lt_status_now == [1, 0, 0, 0, 0] or lt_status_now == [0, 0, 0, 0, 1]:
                    step = d_step
                


                if lt_status_now == [1, 1, 1, 1, 0] or lt_status_now == [1, 1, 1, 1, 1] \
                or lt_status_now == [0, 1, 1, 1, 1]:    
                    if (time.time() - last_time) > 5: # legutobbi vonal triggerelt megallas utan

                        if not reset_active:
                            bw.stop()
                            print("Vonal triggerelt magallas")
                        else:
                            print("Latott vonalat, de nem allt meg")

                        client.publish(carManagement, "update") # a megfelelo helyen erre indul az empty es a fill
                        last_time = time.time()

                        if not reset_active: # ha epp reset van, akkor ne dekkoljon annyit a vonalakon, siessen vissza (ez azert lehet, mert reset alatt, semmi nem fugg a vonalon toltott idotol)

                            for i in range(40): # pontosan 2 sec delay
                                time.sleep(0.05) # = 50ms
                                if blc.getAnimation() == BottleLedControl.ANIMATION_EMPTY: # akkor ha a belso vonalon van :S ez igy nagyon nem jo; Ezt sohsem szabadna egy jol strukturalt koban elofordulnia, hogy a LED vezerlo szol bele az auto vezerlesebe... ez nagyon nagyon nagyon rossz otlet; ha valaki foglalkozik a jovoben a koddal, ezt mindenkeppen oldja meg szepen!!
	                                pause_event.wait() # ez azert kell, mert a pause-nak ezt a 2sec-es delay-t is pauseolnia kellene, de csak akkor amikor bottle empty jonne; elvileg meg vagyunk allva, szoval nem okozhat problemat

                            continue # ha ez nincs itt, akkor az van hogy....
                                     # ha a fenn levo time.sleep alatt nyomunk egy terminate-t, vagy pause-t, vagy barmi mast, ami miatt meg kellene allnia ez alatt a 2 sec alatt,
                                     # akkor is innen folytatodna, es az ido letelte utan, elofordulhat hogy rant egyet a szervon
                                     # ha ez itt van, akkor ujra kiertekeli a felteteleket, es nem 'nyekken' a szervo egyet
                                     # mivel ez legfelulre ugrik vissza, ezert a delay nem fut le, es egybol tud korrigalni az auto

                # keep straight
                if lt_status_now == [0, 0, 1, 0, 0]:
                    turning_angle = 90
                    
                # turn right
                elif lt_status_now in ([0, 1, 1, 0, 0], [0, 1, 0, 0, 0], [1, 1, 0, 0, 0], [1, 0, 0, 0, 0]):
                    turning_angle = int(90 - step)
                    
                # turn left
                elif lt_status_now in ([0, 0, 1, 1, 0], [0, 0, 0, 1, 0], [0, 0, 0, 1, 1], [0, 0, 0, 0, 1]):
                    turning_angle = int(90 + step)
                    

                if not turning_angle: # ha nem latja a vonalat, menjen egyenesen... ugyan mi baj lehet?
                    turning_angle = 90

                fw.turn(turning_angle)
            
            time.sleep(0.005)
        
        except KeyboardInterrupt:
            return
        
        except:
            traceback.print_exc()


def destroy():
    bw.stop()
    fw.turn(90)



def shutdown_system(): # called by timer
        print("Shutting down system...")
        os.system('systemctl poweroff') # this will eventually issue a sigint to us, and we'll shutdown properly as well

shutdown_timer = None


'''
MQTT Cuccok
'''
def on_connect(client, userdata, flag, rc):
    print("Connected!", str(rc))

    client.subscribe(carManagement)
    client.subscribe("stop_system")
    client.subscribe("start_system")

fill_paused = False # ez egy nagyon nagyon nagyon rosz megoldas.... de szorit az ido
def on_message(client, userdata, msg):
    global stop_active,reset_active,pause_event
    global fill_paused # ez is ronda... rosz... csunya...
    global shutdown_timer # ez rosszabb

    print("Topic: ", msg.topic + " Message: " + str(msg.payload))


    if msg.topic == carManagement:

        if msg.payload == "start":
            stop_active = False
            print(obstacle)
            print(stop_active)

        elif msg.payload == "stop":
            stop_active = True

        elif msg.payload == "stopAndBlink":
            stop_active = True
            lc.setAnimation("battery",ledcontrol.LEDAnimationError())
            time.sleep(10)
            pause_event.wait() # wait for pause to set
            lc.setAnimation("battery",ledcontrol.LEDAnimationGood())
            client.publish("forklift_power_error_reset")

        elif msg.payload == "startFill":
            fill_paused = False # ezt is csak azert, ha a resume full nem jott volna meg, akkor ez a resz ne bugoljon be
            blc.startFill(True,False) # ez se csinaljon auto unpause-t, mert akkor ha megall a vonalon mielott toltene, es pause-t kap, akkor elkezdene feltoltodni

        elif msg.payload == "stopFill": # ez csak pause
            fill_paused = True
            blc.pause()

        elif msg.payload == "resumeFill":
            fill_paused = False
            blc.resume()

        elif msg.payload == "emptyBottle":
            fill_paused = False # csak iderakom mert csak
            blc.startEmpty(True,False) # ne legyen auto unpause amikor indul ez az anim, azert, hogy ha akkor pauseolunk amikor a vonalra er, ne menjen le az anim, amig nem tolunk unpause-t


        elif msg.payload == "startReset": # ezt kapod akkor, ha futas kozben megnyomtak a start gombot, azaz az autonak a helyere kell mennie
            fill_paused = False # hogyha pause_fill utan jon a reset, akkor ezt is reseteljuk, es ne ragadjon be
            blc.startWipe() # letorli szepen a flakon ledeket
            lc.setAnimation("battery",carconfig.getResetAnimation()) # azt a villogast csinalja
            stop_active = False # elinditja az autot, ha esetleg meg lenne allva
            reset_active = True # vonal skippeles be

        elif msg.payload == "stopReset": # ezt a demo megallitasa utan kell kapni
            lc.setAnimation("battery",ledcontrol.LEDAnimationGood())  # megalllitja azt a villogast
            blc.setDefault()  # felkapcsolja a legalso piros ledet
            reset_active = False # vonal skippeles ki

        elif msg.payload == "terminate": # stop_system-nel van
            stop_active = True
            fill_paused = False # hogyha a terminate pause fill alatt jon, akkor azt is resetelni kell
            reset_active = False # vonal skippeles ki
            pause_event.set() # unblock paused stuff
            lc.setAnimation("battery",ledcontrol.LEDAnimationOff())
            blc.setOff() # auto unpause

        elif msg.payload == "initLED": # start_system
            stop_active = True # pause -> gateway kapcsolat megszakad -> terminate -> start_system-re az auto elindulna, ugyhogy allitsuk meg
            fill_paused = False # tank animacio unpause lock ki
            reset_active = False # vonal skippeles ki
            pause_event.set() # unblock paused stuff.... ilyent start_system-re kapunk
            lc.setAnimation("battery",ledcontrol.LEDAnimationGood())
            blc.setDefault()

        elif msg.payload == "pause":
            pause_event.clear() # sets blocking
            blc.pause()

        elif msg.payload == "unpause":
            pause_event.set()
            if not fill_paused: # ez azert van, hogyha volt egy pause/unpause a tank liquid error alatt, akkor ne induljon el a feltoltes
                blc.resume()

    # azert nem a terminate-t hasznalom, mert nem akarok abba meg plusz dologokat beleirogatni, eleg ha az csak az auto lelkivilagalval foglalkozik
    # tovabba ott az uzenetek se teljesen utalnak arra, hogy minek kellene tortennie
    # illetve ennek akkor is mukodnie kell, ha a gateway nem elerheto valamilyen okbol (becrashelt, kilepett, stb.)
    # ha lehal a gateway akkor nincs broker es akkor nincs shutdown

    elif msg.topic == "start_system": # cancel shutdown timer

        if shutdown_timer:
            shutdown_timer.cancel()
            print("Shutdown canceled")

    elif msg.topic == "stop_system": # start shutdown timer

        shutdown_timer = threading.Timer(15,shutdown_system)
        shutdown_timer.start()
        print("System shutdown in 15s! Use start_system to cancel.")



def on_publish(client, userdata, mid):
    print("Message published: " + str(mid))


def on_disconnect(client, userdata, result):
    global stop_active
    if result != 0:
        #logolas!
        print("A kocsi es broker kozti kommunikacio megszakadt.")
        stop_active = True
        
        if(not MQTTReconnect()):    
            print("A kapcsolodas nem sikerult, az alkalmazas leall...")
            #alkalmazast kikapcsolni
            return
        else:
            stop_active = False
        

if __name__ == '__main__':
    #global client, stop_active
    
    try:
	setup()
	
	if init_mqtt():
            client.loop_start()
            main()
        else:
            print "A kapcsolodas nem sikerult az mqtt brokerhez"

    except KeyboardInterrupt:
        print("Keyboard Interrupt")
            
    except SystemExit:
        os._exit(0)
        
    except:
        logging.debug(traceback.print_exc())
    
    finally:
        if shutdown_timer:
            shutdown_timer.cancel()

        client.disconnect()
        stop_active = True
        destroy()
	blc.shutdown()
	lc.shutdown()

