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

poll_interval = imu.IMUGetPollInterval()
print("Recommended Poll Interval: %dmS" % poll_interval)

#Filtro passa bajos Apartado1

etapes = 20
historyX = [0] * etapes
historyY = [0] * etapes
historyZ = [0] * etapes
last_index = 0
#coef = ar.array('i',[-435,-745,-1002,-884,-162,1224,3085,4997,6435,6970,6435,4997,3085,1224,-162,-884,-1002,-745,-435])
coef = ar.array('i',[
     283,    546,    872,   1247,   1652,   2061,   2448,   2785,   3046,
     3211,   3268,   3211,   3046,   2785,   2448,   2061,   1652,   1247,
      872,    546,    283])
#123 etapas
#coef = ar.array('i',[-1650,26,23,18,11,2,-8,-21,-35,-50,-67,-84,-102,-120,-139,-157,-174,-191,-206,-220,-232,-241,-248,-252,-252,-249,-243,-232,-218,-199,-176,-149,-117,-82,-42,2,49,100,154,211,270,332,395,459,524,589,653,716,778,838,895,949,1000,1047,1089,1126,1159,1186,1204,1223,1232,1236,1232,1223,1204,1186,1159,1126,1089,1047,1000,949,895,838,778,716,653,589,524,459,395,332,270,211,154,100,49,2,-42,-82,-117,-149,-176,-199,-218,-232,-243,-249,-252,-252,-248,-241,-232,-220,-206,-191,-174,-157,-139,-120,-102,-84,-67,-50,-35,-21,-8,2,11,18,23,26,1650])
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
        accZ = accZ + (historyZ[index] * coef[i])
    accX = (accX / pow(2,16))*2
    accY = (accY / pow(2,16))*2
    accZ = (accZ / pow(2,16))*2
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
    angX = math.degrees(math.acos(accX)) - 90
    angY = math.degrees(math.acos(accY)) - 90

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
    print("Gx: %1.3f Gy: %1.3f Gz: %1.3f - angX = %fº , angY = %fº SampleTime = %f ms - IMUTime = %f" % (accX,accY,accZ,angX,angY,lapsetime, timeIMU), end = '\r')
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
