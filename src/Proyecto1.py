#!/usr/bin/python
from sense_hat import SenseHat
from datetime import datetime
from datetime import time
import sys, getopt

sys.path.append('.')
import threading
import RTIMU
import os.path
import time
import math

sense = SenseHat()

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
    while True:
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
    return

def saveData():
    print(" ", end = "\n")
    print("Esperando joystick",end='\n')
    event = sense.stick.wait_for_event()
    fGx = open("GxData.txt", "a")
    fGx.write(datosGx)
    fGx.close()
    dtimend = datetime.now()
    timetotal = dtimeini.microsecond - dtimend.microsecond
    mps = (dtimeini.microsecond)
    print("Datos grabados en GxData.txt. Tiempo = %i us. Muestras = %i" % (timetotal,sample),end='\n')
    print("Tiempo = %i us. Tiempo end = %i" % (dtimeini.microsecond,dtimend.microsecond), end = "\n")
    print("SPS = %f" % sample, end = "\n")
    
    return

#configuracion del thread
global datosGx, Gx, Gy, Gz, sample, timeini, timend
datosGx = ""
sample = 0
Gx = 0
Gy = 0
Gz = 0

threading.Thread(target=saveData).start()
threading.Thread(target=showrow).start()

#Bucle de ejecucion
while True:
  timeIni = datetime.now()
  if imu.IMURead():
    data = imu.getIMUData()
    sample += 1
    #Se obtiene el dato de aceleracion en la variable accel
    accel = data["accel"]
    Gx = accel[0]
    Gy = accel[1]
    Gz = accel[2]
    #Se guardan los datos para tratamiento posterior
    datosGx = datosGx + ("%f, " %Gx)
    #Tiempo de espera
    time.sleep(poll_interval*1.0/1000.0)
    timeEnd = datetime.now()
    c = (timeEnd - timeIni)/1000
    print("Gx: %1.4f - Gy: %1.4f - Gz: %1.4f - Samp = %i - Time: %i ms " % (Gx,Gy,Gz,sample,c.microseconds),end='\r')



