#!/usr/bin/env python2
from LipoMonitor import LipoMonitor as lipo
import time
import datetime
import threading

def liponoise_loop():
    k = threading.Thread(target=liponoise())
    k.setDaemon(True)
    k.start()

def liponoise():
    try:
        i = 0
        j = 0
        data_array = 100 * [0]
        time_now = datetime.datetime.now()
        f = open("liponoise.log", 'w')
        while True:
            while i < 100:
                data = lipo.calculate_measurement("voltage")
                date_data = datetime.datetime.now() - time_now
                data_array[i] = unicode(date_data)
                i = i + 1
                data_array[i] = data
                i = i + 1
                time.sleep(0.05)
            i = 0
            j = j + 1
            k = 0
            for item in data_array:
                f.write("%s " % item)
                k = k + 1
                if k % 2 == 0:
                    f.write("\n")
            if j == 100:
                f.close()
                break

    except Exception, e:
        print("Liponoise fail")
        print(e)
        f.close()

#if __name__ == '__main__':
#    liponoise()


