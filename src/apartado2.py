#!/usr/bin/python
from sense_hat import SenseHat
from datetime import datetime
from datetime import time
from threading import Event, Thread
import sys, getopt
import array as ar

sys.path.append('.')
import threading
import _thread
import RTIMU
import os.path
import os
import time
import math

sense = SenseHat()
event = Event()

Gx = 0          #almacena dato x Acelerometro
Gy = 0          #almacena dato y Acelerometro
Gz = 0          #almacena dato z Acelerometro
timeIMU = 0     #Tiempo de proceso de la adquisicion de datos del IMU
datosGx = ""    #Variable donde almacenar el array de muestras.
datosGy = ""    #Variable donde almacenar el array de muestras.
datosGz = ""    #Variable donde almacenar el array de muestras.
stopthread3 = 0        #VFlag de parada de los procesos
stopthread2 = 0
stopthread1 = 0

historyX = []
historyY = []
historyZ = []
angX = 0
angY = 0

SETTINGS_FILE = "RTIMULib"

print("Using settings file " + SETTINGS_FILE + ".ini")
if not os.path.exists(SETTINGS_FILE + ".ini"):
  print("Settings file does not exist, will be created")

s = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(s)

print("IMU Name: " + imu.IMUName())

if (not imu.IMUInit()):
    print("IMU Init Failed")
    sys.exit(1)
else:
    print("IMU Init Succeeded")

# this is a good time to set any fusion parameters

imu.setSlerpPower(0.02)
imu.setGyroEnable(False)
imu.setAccelEnable(True)
imu.setCompassEnable(False)

#Filtro passa bajos Apartado1

etapes = 20
historyX = [0] * etapes
historyY = [0] * etapes
historyZ = [0] * etapes
last_index = 0
#coef = ar.array('i',[-435,-745,-1002,-884,-162,1224,3085,4997,6435,6970,6435,4997,3085,1224,-162,-884,-1002,-745,-435])
coef = ar.array('i',[
     -526,   -720,   -727,   -449,    164,   1090,   2232,   3424,   4471,
     5189,   5444,   5189,   4471,   3424,   2232,   1090,    164,   -449,
     -727,   -720,   -526])

def SampleFilter_put ():
    global historyX,historyY, historyZ, last_index
    if (last_index == etapes):
        last_index = 0
    historyX[last_index] = Gx
    historyY[last_index] = Gy
    historyZ[last_index] = Gz
    last_index = last_index + 1

#Funcion para la convolución
def SampleFilter_get ():
    global last_index, coef, accX,accY,accZ

    index = last_index
    i = 0
    accX = 0
    accY = 0
    accZ = 0
    for i in range(etapes):
        if index != 0:
            index = index - 1
        else:
            index = etapes -1
        accX = accX + (historyX[index] * coef[i])
        accY = accY + (historyY[index] * coef[i])
    accX = (accX / pow(2,16))*1.923
    accY = (accY / pow(2,16))*1.923
    accZ = (accZ / pow(2,16))*1.923
    #print ("accX = %f , accY = %f , accZ = %f" %(accX, accY, accZ), end = '\r')
    return

#Funcion para calculo del ángulo
def angulos():
    global angX, accX, accY, angY
    if (accX > 1):
        accX = 1
    elif (accX < -1):
        accX = -1
    if (accY > 1):
        accY = 1
    elif (accY < -1):
        accY = -1
    angX = math.degrees(math.acos(accX)) -90
    angY = math.degrees(math.acos(accY)) -90

#########################################################################

#Declaracion Thread 1
class myThread (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
      #Se ejecuta la función de adquisición de muestras
      print ("Starting " + self.name)
      while stopthread1 == 0:
          adquisitionData(15)
      print ("\nExiting " + self.name)

#Declaracion Thread 2
class myThread2 (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
      print ("Starting " + self.name)
      while stopthread2 == 0:
          Dataget(12)
      print ("\nExiting " + self.name)


#Funcion del thread 1
def adquisitionData(tiempo):
    t0 = time.time()
    SampleFilter_put()
    SampleFilter_get ()
    angulos()
    #Se setean el flag de thread para permitir al trhead de adquisición, tomar el dato.
    event.set()
    time.sleep(tiempo/1000.0)
    lapsetime = ((time.time() - t0) * 1000 )
    print("Gx: %1.2f Gy: %1.2f Gz: %1.2f - angX = %2.1fº , angY = %2.1fº SampleTime = %f ms - IMUTime = %f" % (accX,accY,accZ,angX,angY,lapsetime, timeIMU), end = '\r')
#Funcion del thread 2
def Dataget (tiempo):
    global Gx, Gy, Gz, timeIMU
    event.wait() # Blocks until the flag becomes true.
    t0 = time.time()
    i = 0
    while (imu.IMURead() == 0):
        time.sleep(0.25/1000.0)

    data = imu.getIMUData()
    #Se obtiene el dato de aceleracion en la variable accel
    accel = data["accel"]
    Gx = accel[0]
    Gy = accel[1]
    Gz = accel[2]
    timeIMU = (time.time() - t0) * 1000
    #if (timeIMU > (tiempo)):
    #    print ("IMU Delay.")
    event.clear() # Resets the flag.

# Create new threads
thread1 = myThread(1, "Thread-1")
thread2 = myThread2(2, "Thread-2")

# Start new Threads
thread2.start()
thread1.start()
#thread4.start()


print ("\nExiting Main Thread")
