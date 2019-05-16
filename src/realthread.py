#!/usr/bin/python
from sense_hat import SenseHat
from datetime import datetime
from datetime import time
from threading import Event, Thread
import sys, getopt

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
numSamples = 0 #Numero de muestras tomadas
datosGx = ""    #Variable donde almacenar el array de muestras.
datosGy = ""    #Variable donde almacenar el array de muestras.
datosGz = ""    #Variable donde almacenar el array de muestras.
stop = 0        #VFlag de parada de los procesos
stopthread2 = 0
stopthread1 = 0

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
imu.setGyroEnable(True)
imu.setAccelEnable(True)
imu.setCompassEnable(True)

poll_interval = imu.IMUGetPollInterval()
print("Recommended Poll Interval: %dmS" % poll_interval)

#########################################################################
#Declaracion Thread SaveData
class SaveDataTrhead (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
      global stopthread2,stopthread1
      print ("\nStarting " + self.name)
      #Se crea un fichero de datos nuevo vacio.
      print("\nEsperando joystick para guardar Datos:")
      event = sense.stick.wait_for_event()
      if os.path.exists("GxData.txt"):
           print("\nSe elimina GxData.txt")
           os.remove("GxData.txt")
      else:
           print("\nSe crea : GxData.txt")
           fGx = open("GxData.txt", "a")
           fGx.write(datosGx)
      print ("\nExiting " + self.name)
      stopthread2 = 1
      time.sleep(500/1000)
      stopthread1 = 1

#Declaracion Thread 1
class myThread (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
      #Se ejecuta la función de adquisición de muestras
      print ("\nStarting " + self.name)
      while stopthread1 == 0:
          adquisitionData(12)
      print ("\nExiting " + self.name)


#Declaracion Thread 2
class myThread2 (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
      print ("\nStarting " + self.name)
      while stopthread2 == 0:
          Dataget(10)
      print ("\nExiting " + self.name)

#Funcion del thread 1
def adquisitionData(tiempo):
    global datosGx, datosGy, datosGz, numSamples
    t0 = time.time()
    datosGx += ("%f, " %Gx)
    numSamples = numSamples +1
    event.set()
    time.sleep(tiempo/1000.0)
    lapsetime = ((time.time() - t0) * 1000 )
    print("Gx: %1.4f Gy: %1.4f Gz: %1.4f - #Samples = %i SampleTime = %f ms - IMUTime = %f" % (Gx,Gy,Gz,numSamples,lapsetime, timeIMU), end = '\r')

#Funcion del thread 2
def Dataget (tiempo):
    global Gx, Gy, Gz, timeIMU
    event.wait() # Blocks until the flag becomes true.
    t0 = time.time()
    if imu.IMURead():
        data = imu.getIMUData()
        #Se obtiene el dato de aceleracion en la variable accel
        accel = data["accel"]
        Gx = accel[0]
        Gy = accel[1]
        Gz = accel[2]
        timeIMU = (time.time() - t0) * 1000
        #print ("IMU Time : %f ms" %timeIMU)
    event.clear() # Resets the flag.

# Create new threads
thread1 = myThread(1, "Thread-1")
thread2 = myThread2(2, "Thread-2")
thread3 = SaveDataTrhead(2, "SaveDataTrhead")

# Start new Threads
thread1.start()
thread2.start()
thread3.start()
print ("\nExiting Main Thread")
