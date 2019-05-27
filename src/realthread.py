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
acc = 0
history = []

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

etapes = 123
history = [0] * etapes
last_index = -1
#coef = ar.array('i',[-435,-745,-1002,-884,-162,1224,3085,4997,6435,6970,6435,4997,3085,1224,-162,-884,-1002,-745,-435])
#123 etapas
coef = ar.array('i',[-1650,26,23,18,11,2,-8,-21,-35,-50,-67,-84,-102,-120,-139,-157,-174,-191,-206,-220,-232,-241,-248,-252,-252,-249,-243,-232,-218,-199,-176,-149,-117,-82,-42,2,49,100,154,211,270,332,395,459,524,589,653,716,778,838,895,949,1000,1047,1089,1126,1159,1186,1204,1223,1232,1236,1232,1223,1204,1186,1159,1126,1089,1047,1000,949,895,838,778,716,653,589,524,459,395,332,270,211,154,100,49,2,-42,-82,-117,-149,-176,-199,-218,-232,-243,-249,-252,-252,-248,-241,-232,-220,-206,-191,-174,-157,-139,-120,-102,-84,-67,-50,-35,-21,-8,2,11,18,23,26,1650])
def SampleFilter_put ():
    global history, last_index
    if (last_index == etapes-1):
        last_index = 0
    history[last_index + 1] = Gx
    last_index = last_index + 1


def SampleFilter_get ():
    global last_index, coef, acc, i

    index = last_index
    i = 0
    acc = 0
    for i in range(etapes):
        if index != 0:
            index = index - 1
        else:
            index = etapes -1
        acc = acc + (history[index] * coef[i])
    acc = acc / pow(2,16)
    print ("acc = %f" %acc)

    return

    #Callback the thread para mostrar orientaciÃ³n por pantalla
def showrow():
    estado = 0;
    timeIni = int(round(time.time() * 1000))
    #Se define el angulo de la imagen a mostrar.
    if (Gz >= 0.5 and Gz > 0):
        img = sense.load_image("dentro.png")
    elif (Gz <= -0.5 and Gz < 0):
        img = sense.load_image("fuera.png")
    else:
        img = sense.load_image("flecha.png")
        if (acc>= 0.95):
            sense.rotation = 90
        elif (acc<=-0.95):
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
    #print ("Gx: %f - Gy: %f - Gz: %f - Time: %i" % (Gx,Gy,Gz,c) )


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

#Declaracion Thread 2
class showRowThread (threading.Thread):
   def __init__(self, threadID, name):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
      print ("Starting " + self.name)
      while stopthread2 == 0:
         showrow ()
      print ("\nExiting " + self.name)

#Funcion del thread 1
def adquisitionData(tiempo):
    global datosGx, datosGy, datosGz, numSamples, accelArrx, Gx, rawGx
    offsetGx = 0
    t0 = time.time()
    #Filtrado pasa bajos para showrow
    SampleFilter_put()
    SampleFilter_get ()
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
    #print("Gx: %1.4f Gy: %1.4f Gz: %1.4f - #Samples = %i SampleTime = %f ms - IMUTime = %f" % (Gx-offsetX,Gy,Gz,numSamples,lapsetime, timeIMU), end = '\r')
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
thread3 = SaveDataTrhead(2, "SaveDataTrhead")
thread4 = showRowThread(2, "showRowThread")

# Start new Threads
thread3.start()
time.sleep(100/1000)
thread2.start()
thread1.start()
thread4.start()


print ("\nExiting Main Thread")
