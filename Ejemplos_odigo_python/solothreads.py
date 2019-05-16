#!/usr/bin/python

import threading
from threading import Event, Thread
import time

#Declaracion Thread 1
class myThread (threading.Thread):
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
      while True:
          print ("Starting " + self.name)
          adquisitionData(20)
          print ("Exiting " + self.name)

#Declaracion Thread 2
class myThread2 (threading.Thread):
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
      while True:
          print ("Starting " + self.name)
          Dataget(10)
          print ("Exiting " + self.name)

event = Event()
#Funcion del thread 1
def adquisitionData(tiempo):
    t0 = time.time()
    event.set()
    time.sleep(tiempo/1000.0)
    lapsetime = ((time.time() - t0) * 1000 )
    print("Time Thread1 = %f ms" % (lapsetime))

#Funcion del thread 2
def Dataget (tiempo):
    event.wait() # Blocks until the flag becomes true.
    t0 = time.time()
    time.sleep(tiempo/1000.0)
    c = (time.time() - t0) * 1000
    print("IMU Data - Time: %3.3f ms  " % (c), end ='\n')
    event.clear() # Resets the flag.

# Create new threads
thread1 = myThread(1, "Thread-1", 1)
thread2 = myThread2(2, "Thread-2", 2)

# Start new Threads
thread1.start()
thread2.start()

print ("Exiting Main Thread")
