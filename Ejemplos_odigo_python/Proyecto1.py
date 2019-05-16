#!/usr/bin/python
from sense_hat import SenseHat
from datetime import datetime
from datetime import time
import sys, getopt

sys.path.append('.')
import threading
import _thread
import RTIMU
import os.path
import time
import math

sense = SenseHat()

stop = 0
Gx = 0
Gy = 0
Gz = 0
c = 0

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
print("Recommended Poll Interval: %dmS\n" % poll_interval)

#Callback the thread para mostrar orientación por pantalla
def showrow():
    estado = 0;
    while (stop == 0):
        timeIni = int(round(time.time() * 1000))
        #Se define el angulo de la imagen a mostrar.
        if (Gz >= 0.5 and Gz > 0):
            img = sense.load_image("dentro.png")
        elif (Gz <= -0.5 and Gz < 0):
            img = sense.load_image("fuera.png")
        else:
            img = sense.load_image("flecha.png")
            if (Gx>= 0.95):
                sense.rotation = 90
            elif (Gx<=-0.95):
                sense.rotation = 270
            elif (Gy>= 0.95):
                sense.rotation = 180
            elif (Gy<= -0.95):
                sense.rotation = 0
        #Se muestra la imagen RGB
        if (estado != sense.rotation):
            sense.set_pixels(img)
        timeEnd = int(round(time.time() * 1000))
        c = (timeEnd - timeIni)
        #print ("Gx: %f - Gy: %f - Gz: %f - Time: %i" % (Gx,Gy,Gz,c))

def saveData():
    global stop #Se utiliza para detener la ejecucion del programa cuando acba el thread
    stop = 0
    milli_secIni = int(round(time.time() * 1000))
    print("\nEsperando joystick\n")
    event = sense.stick.wait_for_event()
    fGx = open("GxData.txt", "a")
    fGx.write(datosGx)
    milli_secEnd = int(round(time.time() * 1000))
    fGx.close()
    milli_secTotal = int(milli_secEnd-milli_secIni)
    SPS = sample/(milli_secTotal/1000)
    print("Datos grabados en GxData.txt. Tiempo = %i ms. Muestras = %i, SPS = %f" % (milli_secTotal,sample,SPS),end='\n')
    stop = 1
    return

class myThread (threading.Thread):
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
      while True:
          adquisitionData()
#Funcion que solicita la adquisición de datos de forma periodica según fm en milisegundos.
fm = 1000#en milisegundos
datosGx = ""
sample = 0
def adquisitionData():
    global sample, flag
    t0 = time.time()
    #Se guardan los datos para tratamiento posterior
    #datosGx += ("%f, " %Gx)
    sample += 1
    flag = 1
    time.sleep(fm/1000.0)
    lapsetime = ((time.time() - t0) * 1000 )
    print("\n Gx: %1.8f - Gy: %1.8f - Gz: %1.8f - Samp = %i - SampTime = %f ms" % (Gx,Gy, Gz,sample,lapsetime),end = '\n')




#Obtiene los datos del IMU
class myThread2 (threading.Thread):
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
       while True:
          Dataget()

flag = 1
def Dataget ():
    global Gx
    global Gy
    global Gz
    global c
    global flag
    #timeIni = int(round(time.time() * 1000000))
    t0 = time.time()
    if (imu.IMURead() and flag == 1):
        data = imu.getIMUData()
        #Se obtiene el dato de aceleracion en la variable accel
        accel = data["accel"]
        Gx = accel[0]
        Gy = accel[1]
        Gz = accel[2]
        #Tiempo de espera
        #time.sleep(poll_interval*1.0/1000.0)
        c = (time.time() - t0) * 1000
        print("IMU Data - Time: %3.3f ms  " % (c), end ='\n')
        flag = 0


# Create new threads
thread1 = myThread(1, "Thread-1", 1)
thread2 = myThread2(2, "Thread-2", 2)

# Start new Threads
thread1.start()
thread2.start()

print ("Exiting Main Thread")
