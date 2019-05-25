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
stopthread3 = 0        #VFlag de parada de los procesos
stopthread2 = 0
stopthread1 = 0
accelArrx = []
offsetX = 0     #Variable del valor de offset para Eje X
rawGx = ""

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
#Rutina de autoejecución
    def run(self):

        global stopthread2,stopthread1, stopthread3,offsetX

        print ("\nStarting " + self.name)
        #Se crea un fichero de datos nuevo vacio.
        if os.path.exists("GxData.txt"):
            print("\nSe elimina GxData.txt anterior.")
            os.remove("GxData.txt")
            os.remove("GxRawData.txt")
        print("\nSe crea : GxData.txt")
        fGx = open("GxData.txt", "a")
        fRawGx = open("GxRawData.txt", "a")
        print("\nEsperando joystick para opcion:")
        #Bucle de captura de entradas del joystick.
        while stopthread3 == 0:
            event = sense.stick.wait_for_event()
            #Boton central: Calibrar acelerometro en posicion de reposo.
            if (event.direction == "middle"):
                suma = 0
                for x in accelArrx:
                    suma = suma + x
                offsetX = suma / len(accelArrx)
                print("\nOffset en X = %f."% offsetX, end='\n')
            #Otro Boton: Guardar fichero y cerrar programa.
            else:
                fGx.write(datosGx)
                fRawGx.write(rawGx)
                print ("\nExiting " + self.name)
                stopthread2 = 1
                time.sleep(500/1000)
                stopthread1 = 1
                stopthread3 =  1

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
    global datosGx, datosGy, datosGz, numSamples, accelArrx, Gx, rawGx
    offsetGx = 0
    t0 = time.time()
    accelArrx.append (Gx)
    #secorrige el valor de Gx
    if (offsetX != 0):
        offsetGx = Gx - offsetX
        if (abs(offsetGx) < 0.005):
            offsetGx = 0
        datosGx += ("%f, " % (offsetGx))
        rawGx  += ("%f, " % (Gx))
        numSamples = numSamples +1
    #Se setean el flag de thread para permitir al trhead de adquisición, tomar el dato.
    event.set()
    time.sleep(tiempo/1000.0)
    lapsetime = ((time.time() - t0) * 1000 )
    print("Gx: %1.4f Gy: %1.4f Gz: %1.4f - #Samples = %i SampleTime = %f ms - IMUTime = %f" % (Gx-offsetX,Gy,Gz,numSamples,lapsetime, timeIMU), end = '\r')
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
    if (timeIMU > (tiempo)):
        print ("IMU Delay.")
    event.clear() # Resets the flag.

# Create new threads
thread1 = myThread(1, "Thread-1")
thread2 = myThread2(2, "Thread-2")
thread3 = SaveDataTrhead(2, "SaveDataTrhead")

# Start new Threads
thread3.start()
time.sleep(100/1000)
thread2.start()
thread1.start()


print ("\nExiting Main Thread")
