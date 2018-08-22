#!/usr/bin/python
import sys
import time 
import datetime 
import RPi.GPIO as io 
import select
import SectorAdminSite
import RFIDDataAccess
import subprocess
import glob
import os
import Adafruit_CharLCDPlate
from Adafruit_I2C import Adafruit_I2C
import locale
import math

class MachineLogic:

    rfid =0
    prevRFID = 0
    billingRFID = 0
    cashRFID = 7898934
    machineID = 1 #4
    isbusy = False
    DebugMode = False
    fullname= ''
    accruingDue = 0.0
    linecuts = 0

    LASERPIN = 25    #// Laser power supply ACTIVE LOW
    LASERENABLEPIN1 = 23 #// Using two pins to trigger the relay to ensure enough current
    LASERENABLEPIN2 = 24 #// Using two pins to trigger the relay to ensure enough current
    LASERONPIN = 17
    JOB_END_TIME = 5 #//Time beam must be off before a job is ended and reported
    MIN_REPORT_TIME = 5 #//Minimum job length to generate a usage report

    state = [ "DISABLED",  "VERIFYING",  "ENABLED",  "ENROLLING"]
    currentstate = "DISABLED"
    laseron = False
    laseroff1 = False
    laseroff2 = False
    laseroff3 = False
    laserstarttime = time.localtime()
    lastlaserontime= datetime.datetime.now()
    lastlaserofftime = lastlaserontime #datetime.datetime.now()# + datetime.timedelta(0,100000)
    jobRunning = False    
    sleepTime = 0.05

    LCDRefresh= False
    
    jobtime = 0
    authService = SectorAdminSite.SectorAdmin()
    access = RFIDDataAccess.DataAccess()
    locale.setlocale(locale.LC_ALL,'')


    lcd = Adafruit_CharLCDPlate.Adafruit_CharLCDPlate()

    prev = -1
    btn = ((lcd.SELECT, 'Select'),
           (lcd.LEFT  , 'Left'  ),
           (lcd.UP    , 'Up'    ),
           (lcd.DOWN  , 'Down'  ),
           (lcd.RIGHT , 'Right' ))

    laserArray =[0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0,
       0,0,0,0,0,0,0,0,0,0]	
    laserReadIndex = 0 
     
       #
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,
       #0,0,0,0,0,0,0,0,0,0,

    def Busy(self):
        return self.isbusy
    
    def Setup(self):

        io.setmode(io.BCM)

        power_pin = 2
        pir_pin = 24
        io.setup(self.LASERPIN, io.IN) 
        io.setup(self.LASERONPIN, io.IN) 
        io.setup(self.LASERENABLEPIN1, io.OUT)
        io.setup(self.LASERENABLEPIN2, io.OUT)
        io.output(self.LASERENABLEPIN1, True)
        io.output(self.LASERENABLEPIN2, True)

        self.currentstate = "DISABLED"
        self.laseron = False
        self.laserstarttime = datetime.datetime.now()
        self.lastlaserontime = self.laserstarttime 
        self.lastlaserofftime = self.lastlaserontime
        self.jobtime = 0
        self.jobRunning = False 
        self.sleepTime = 0.05

        self.lcd.begin(16, 2)	
        self.LCDRefresh = True

    def SetRFID(self, inRFID):
	self.prevRFID = self.rfid
	self.rfid = inRFID

    #// If a job has recently ended, report it
    def ReportJob(self):
        
        #newest = max(glob.iglob('/home/pi/ImageLog/*.jpg'), key=os.path.getctime)
        #print(newest)
        #jpgfile = open(newest).read()
   	amount = 0

	try:
           amount = self.authService.AddMachinePayment(int(self.billingRFID),self.jobtime,self.machineID, 'Laser cut time for {0}'.format(self.jobtime), '')
        except:
	   print('internet connection failed')
        
        #print("{0:0.2f}".format(float(amount)))
        self.accruingDue += float(amount)
        self.LCDRefresh = True
            
    
    def CaptureImage(self):

        subprocess.call("/home/pi/grabPic.sh")


    def CheckBeam(self):

        if self.currentstate== "ENABLED":
            if io.input(self.LASERPIN) == 0 and self.laseron == False and io.input(self.LASERONPIN)== 1 :
                print("beam on")
                self.laseron = True
                self.laserstarttime = datetime.datetime.now()
                self.jobRunning = True 
                self.sleepTime = 0.05
		self.laserReadIndex = 0 
                self.laserArray[self.laserReadIndex] = 1
                self.laserReadIndex += 1 

            elif io.input(self.LASERPIN) == 0 and self.laseron == True and sum(self.laserArray) <> 0:
                print(sum(self.laserArray))
		self.laserArray[self.laserReadIndex] = 1
                self.laserReadIndex += 1
                print('setting {0} value {1}'.format(self.laserReadIndex, 1))
                if self.laserReadIndex == 40:
                   self.laserReadIndex = 0 

            elif io.input(self.LASERPIN) == 1 and self.laseron == True and sum(self.laserArray) <> 0:
		self.laserArray[self.laserReadIndex] = 0
                self.laserReadIndex += 1
                print('setting {0} value {1}'.format(self.laserReadIndex, 0))
                if self.laserReadIndex == 40:
                   self.laserReadIndex = 0 

            elif io.input(self.LASERPIN) == 1  and (datetime.datetime.now()-self.laserstarttime).seconds > self.MIN_REPORT_TIME and self.laseron == True and sum(self.laserArray) == 0: # and (datetime.datetime.now()-self.laserstarttime).seconds > 5:               
                self.sleepTime = 0.05
                #self.CaptureImage()
                self.laseron = False
                timelapse = (datetime.datetime.now()-self.laserstarttime)
                self.jobtime = (float(timelapse.seconds) + float(timelapse.microseconds)/float(1000000)) - 10
                print("job length of {0} seconds".format(self.jobtime))
                self.ReportJob()
                #print(self.linecuts)
                self.lastlaserontime = datetime.datetime.now()
                self.lastlaserofftime = self.lastlaserontime  #datetime.datetime.now() # + datetime.timedelta(0,100000)
                self.jobtime = 0.0
                self.linecuts = 0
                self.jobRunning = False 

    def DoUnAuthorizedContinuousWork(self):
        self.CheckBeam()
        self.UpdateLCD()
        self.CheckButton()
        if io.input(self.LASERONPIN)== 1 and self.currentstate == "DISABLED":
            self.currentstate = "ON"
            self.LCDRefresh = True 
        elif io.input(self.LASERONPIN)== 0 and self.currentstate == "ENABLED":
            self.isbusy = False
            self.currentstate = "DISABLED"
            io.output(self.LASERENABLEPIN1, True)
            io.output(self.LASERENABLEPIN2, True)
            print(self.currentstate)
	    self.billingRFID = 0
	    self.rfid = 0
            self.jobtime = 0.0
            self.accruingDue = 0
            self.LCDRefresh = True        

        self.lcd.setCursor(15,0)
	self.lcd.message('0')
	time.sleep(0.1)
        self.lcd.setCursor(15,0)
	self.lcd.message('-')
	time.sleep(0.1)    
            
        #print(self.currentstate)

    def DoAuthorizedWork(self):
        if self.currentstate == "ON" :
            self.isbusy = True
            self.currentstate = "ENABLED"
            io.output(self.LASERENABLEPIN1, False)
            io.output(self.LASERENABLEPIN2, False)
            print(self.currentstate)
	    self.billingRFID = self.rfid
            self.accruingDue = 0
            self.lcd.clear()
            #self.lcd.message("  Current User  \n" + self.fullname)
            self.lcd.message("     Please     \n       Wait     ")
            user = self.access.GetUserByRFID(self.rfid)
            #self.fullname = user
            self.LCDRefresh = True
            self.laserstarttime = datetime.datetime.now()
            self.lastlaserontime = self.laserstarttime 
            self.lastlaserofftime = self.lastlaserontime
            self.jobRunning = False 
        elif self.currentstate == "ENABLED" and self.laseron <> True:
            self.isbusy = False
            self.currentstate = "ON"
            io.output(self.LASERENABLEPIN1, True)
            io.output(self.LASERENABLEPIN2, True)
            print(self.currentstate)
	    self.billingRFID = 0
	    self.rfid = 0
            self.jobtime = 0.0
            self.accruingDue = 0
            self.LCDRefresh = True
            self.jobRunning = False 


    def UpdateLCD(self):
        if self.LCDRefresh == True:
            if self.accruingDue > 0.00 :
                self.lcd.clear()
                self.lcd.message("Due:$" + "{0:0.2f}".format(float(self.accruingDue))  + "\n" + self.fullname)
            elif self.currentstate== "ENABLED":
                self.lcd.clear()
                print(self.billingRFID)
                self.lcd.message("  Current User  \n" + self.fullname)
            elif self.currentstate== "ON":
                self.lcd.clear() 
                self.lcd.message("  Please Swipe  \n    RFID Tag   ")
            elif self.currentstate== "DISABLED":
                self.lcd.clear() 
                self.lcd.message("  Please Turn  \n  On Machine ")
                #self.lcd.message("  Please Swipe  \n    RFID Tag   ")
                #self.lcd.message("  Laser cutter  \n     Ready    ")


            self.LCDRefresh = False

        if self.DebugMode:
                self.lcd.clear()
                self.lcd.message("{0}".format(self.rfid) + " {0}".format(self.billingRFID) + "\n{0}".format(io.input(self.LASERPIN)) +" {0}".format(self.laseron))


    def SetBillingAccount(self, rfid):
        #if self.currentstate == "ENABLED" and self.laseron <> True:
           #if self.cashRFID == rfid:
           #   self.fullname ="Cash"
           #   self.billingRFID = rfid
           #   self.lcd.clear()
           #   self.lcd.message("  Current User  \n      Cash")
           #else :
              self.fullname = ''
	      try:
	      	data = self.authService.GetUserByRFID(rfid)            
              	self.fullname = data
              	print(self.fullname)
              	self.billingRFID = rfid
              except:
		print('cannot add billing user')

              self.LCDRefresh = True
              #self.lcd.clear()
              #self.lcd.message("  Current User  \n" + self.fullname)

    def CheckButton(self):
        for self.b in self.btn:
	    if self.lcd.buttonPressed(self.b[0]):
                if self.b is not self.prev:
		    print(self.b[1])

		    if self.b[1] == "Down":
                       self.DebugMode = True
		    if self.b[1] == "Up":                  
                       self.DebugMode = False
                       self.LCDRefresh = True

		    self.prev = self.b
