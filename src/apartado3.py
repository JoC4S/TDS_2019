#!/usr/bin/python
from sense_hat import SenseHat
from datetime import datetime
from datetime import time
from threading import Event, Thread
import threading
import _thread
import RTIMU
import os.path
import os
import time
import math
import sys
import getopt
import array as ar


sys.path.append('.')

sense = SenseHat()
event = Event()

Gx = 0          # almacena dato x Acelerometro
Gy = 0          # almacena dato y Acelerometro
Gz = 0          # almacena dato z Acelerometro
timeIMU = 0     # Tiempo de proceso de la adquisicion de datos del IMU
numSamples = 0  # Numero de muestras tomadas
datosGx = 0     # Variable donde almacenar el array de muestras.
datosGy = ""    # Variable donde almacenar el array de muestras.
datosGz = ""    # Variable donde almacenar el array de muestras.
stopthread3 = 0  # VFlag de parada de los procesos
stopthread2 = 0
stopthread1 = 0
accelArrx = []
offsetX = 0     # Variable del valor de offset para Eje X
rawGx = ""
velocidad = 0.0
velanterior = 0
distancia = 0.0
flag = 0
t = [0,0,0]
accX = 0
previa = 0

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

#########################################################################
# Declaracion Thread SaveData
etapes = 20
historyX = [0] * etapes
last_index = 0
coef = ar.array('i', [
     -526,   -720,   -727,   -449,    164,   1090,   2232,   3424,   4471,
     5189,   5444,   5189,   4471,   3424,   2232,   1090,    164,   -449,
     -727,   -720,   -526])


def SampleFilter_put():
    global historyX, last_index
    if (last_index == etapes):
        last_index = 0
    historyX[last_index] = Gx
    last_index = last_index + 1

# Funcion para la convolución


def SampleFilter_get():
    global last_index, coef, accX

    index = last_index
    i = 0
    accX = 0
    for i in range(etapes):
        if index != 0:
            index = index - 1
        else:
            index = etapes -1
        accX = accX + (historyX[index] * coef[i])
    accX = (accX / pow(2, 16))*2
    #print ("accX = %f , accY = %f , accZ = %f" %(accX, accY, accZ), end = '\r')
    return

class SaveDataTrhead (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
# Rutina de autoejecución
    def run(self):

        global stopthread2, stopthread1, stopthread3, offsetX, velocidad, distancia

        print ("\nStarting " + self.name)
        # Se crea un fichero de datos nuevo vacio.
        if os.path.exists("GxRawData.txt"):
            print("\nSe elimina GxRawData.txt anterior.")
            os.remove("GxRawData.txt")
        print("\nSe crea : GxData.txt")
        fRawGx = open("GxRawData.txt", "a")
        print("\nEsperando joystick para opcion:")
        # Bucle de captura de entradas del joystick.
        while stopthread3 == 0:
            event = sense.stick.wait_for_event()
            # Boton central: Calibrar acelerometro en posicion de reposo.
            if (event.direction == "middle"):
                suma = 0
                for x in accelArrx:
                    suma = suma + x
                offsetX = suma / len(accelArrx)
                velocidad = 0
                distancia = 0
                print("\nOffset en X = %f." % offsetX)
            # Otro Boton: Guardar fichero y cerrar programa.
            else:
                fRawGx.write(rawGx)
                print ("\nExiting " + self.name)
                stopthread2 = 1
                time.sleep(500/1000)
                stopthread1 = 1
                stopthread3 = 1

# Declaracion Thread 1


class myThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        # Se ejecuta la función de adquisición de muestras
        print ("Starting " + self.name)
        while stopthread1 == 0:
            adquisitionData(15)
        print ("\nExiting " + self.name)

# Declaracion Thread 2


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

# Funcion del thread 1


def adquisitionData(tiempo):
    global datosGx, datosGy, datosGz, numSamples, accelArrx, Gx, rawGx, previa
    global velocidad, distancia, flag, t, accX
    offsetGx = 0
    t0 = time.time()
    if offsetX == 0:
        accelArrx.append(accX)
    # secorrige el valor de Gx
    if (offsetX != 0):
        offsetGx = accX - offsetX

        # poner filtro pasa bajos a offsetGX

        if (abs(offsetGx) < 0.02):
            offsetGx = 0
        rawGx += ("%f, " % (offsetGx))
        #rawGx += ("%f, " % (Gx))
        numSamples = numSamples + 1
# Se setean el flag de thread para permitir al trhead de adquisición, tomar el dato.
    event.set()
    time.sleep(tiempo/1000.0)
    lapsetime = ((time.time() - t0) * 1000)
    deltav = ((offsetGx * 9.8 * (lapsetime / 1000)))
    deltav += ((offsetGx - previa)/2) * 9.8 * (lapsetime / 1000)
    velocidad = velocidad + deltav
    if (offsetGx == 0) and (abs(velocidad) < 0.05):
        velocidad = 0
    distancia = distancia + (velocidad * lapsetime/1000)
    previa = offsetGx
    #print("Velocidad = %f m/s, Distancia = %f m - #Samples = %i SampleTime = %2.2f ms" % (velocidad, distancia, numSamples, lapsetime), end = '\r')
    print("Velocidad = %f m/s, Distancia = %f m - #Samples = %i SampleTime = %2.2f ms, Gx: %f "  % ( velocidad, distancia, numSamples, lapsetime, accX - offsetX), end = '\r')
# Funcion del thread 2


def Dataget(tiempo):
    global Gx, Gy, Gz, timeIMU
    event.wait()  # Blocks until the flag becomes true.
    t0 = time.time()
    i = 0
    while (imu.IMURead() == 0):
        time.sleep(0.25/1000.0)

    data = imu.getIMUData()
    # Se obtiene el dato de aceleracion en la variable accel
    accel = data["accel"]
    Gx = accel[0]
    Gy = accel[1]
    Gz = accel[2]
    timeIMU = (time.time() - t0) * 1000
    if (timeIMU > (tiempo)):
        print ("IMU Delay.")
    event.clear()  # Resets the flag.
    SampleFilter_put()
    SampleFilter_get()


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
