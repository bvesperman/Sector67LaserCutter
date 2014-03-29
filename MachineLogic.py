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
    machineID = 4
    isbusy = False
    DebugMode = False
    fullname= ''
    accruingDue = 0.0

    LASERPIN = 25    #// Laser power supply ACTIVE LOW
    LASERENABLEPIN1 = 23 #// Using two pins to trigger the relay to ensure enough current
    LASERENABLEPIN2 = 24 #// Using two pins to trigger the relay to ensure enough current
    JOB_END_TIME = 5 #//Time beam must be off before a job is ended and reported
    MIN_REPORT_TIME = 5 #//Minimum job length to generate a usage report

    state = [ "DISABLED",  "VERIFYING",  "ENABLED",  "ENROLLING"]
    currentstate = "DISABLED"
    laseron = False
    laserstarttime = time.localtime()
    lastlaserontime= datetime.datetime.now()
    lastlaserofftime = datetime.datetime.now() + datetime.timedelta(0,100000)
    

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
    def Busy(self):
        return self.isbusy
    
    def Setup(self):

        io.setmode(io.BCM)

        power_pin = 2
        pir_pin = 24
        io.setup(self.LASERPIN, io.IN) 
        io.setup(self.LASERENABLEPIN1, io.OUT)
        io.setup(self.LASERENABLEPIN2, io.OUT)
        io.output(self.LASERENABLEPIN1, False)
        io.output(self.LASERENABLEPIN2, False)

        self.currentstate = "DISABLED"
        self.laseron = False
        self.laserstarttime = datetime.datetime.now()
        self.lastlaserontime = datetime.datetime.now()
        self.jobtime = 0

        
        self.lcd.begin(16, 2)	
        self.LCDRefresh = True

    def SetRFID(self, inRFID):
	self.prevRFID = self.rfid
	self.rfid = inRFID

    #// If a job has recently ended, report it
    def ReportJob(self):
        
        newest = max(glob.iglob('/home/pi/ImageLog/*.jpg'), key=os.path.getctime)
        print(newest)
        jpgfile = open(newest).read()
        amount = self.authService.AddMachinePayment(int(self.billingRFID),self.jobtime,self.machineID, 'Laser cut time for {0}'.format(self.jobtime),jpgfile)
        
        print("{0:0.2f}".format(float(amount)))
        self.accruingDue += float(amount)
        self.LCDRefresh = True
            
    
    def CaptureImage(self):

        subprocess.call("/home/pi/grabPic.sh")


    def CheckBeam(self):
      
        if self.currentstate== "ENABLED":
            if io.input(self.LASERPIN) == 0 and self.laseron == False:
                print("beam on")
                self.laseron = True
                self.laserstarttime = datetime.datetime.now()
            elif io.input(self.LASERPIN) == 1 and self.laseron == True:
                self.laseron = False
                print("beam off")
                timelapse = (datetime.datetime.now()-self.laserstarttime)
                self.jobtime += (float(timelapse.seconds) + float(timelapse.microseconds)/float(1000000))
                self.lastlaserofftime = datetime.datetime.now()
            elif io.input(self.LASERPIN) == 1 and self.laseron == False and self.jobtime > self.MIN_REPORT_TIME:               
                print("job length of {0} seconds".format(self.jobtime))
                #self.CaptureImage()
                self.ReportJob()
                self.lastlaserontime = datetime.datetime.now()
                self.lastlaserofftime = datetime.datetime.now() + datetime.timedelta(0,100000)
                self.jobtime = 0.0

    def DoUnAuthorizedContinuousWork(self):
        self.CheckBeam()
        self.UpdateLCD()
        self.CheckButton()
        
                
    def DoAuthorizedWork(self):
        if self.currentstate == "ENABLED" and self.laseron <> True:
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
        elif self.currentstate == "DISABLED" :
            self.isbusy = True
            self.currentstate = "ENABLED"
            io.output(self.LASERENABLEPIN1, False)
            io.output(self.LASERENABLEPIN2, False)
            print(self.currentstate)
	    self.billingRFID = self.rfid
            self.accruingDue = 0
            user = self.access.GetUserByRFID(self.rfid)
            self.fullname = user
            self.LCDRefresh = True

            

    def UpdateLCD(self):
        if self.LCDRefresh == True:
            if self.accruingDue > 0.00 :
                self.lcd.clear()
                self.lcd.message("Due:$" + "{0:0.2f}".format(float(self.accruingDue))  + "\n" + self.fullname)
            elif self.currentstate== "ENABLED":
                self.lcd.clear()
                self.lcd.message("  Current User  \n" + self.fullname)
            elif self.currentstate== "DISABLED":
                self.lcd.clear()
                self.lcd.message("  Laser cutter  \n     Ready    ")

            self.LCDRefresh = False

        if self.DebugMode:
                self.lcd.clear()
                self.lcd.message("{0}".format(self.rfid) + " {0}".format(self.billingRFID) + "\n{0}".format(io.input(self.LASERPIN)) +" {0}".format(self.laseron))


    def SetBillingAccount(self, rfid):
        if self.currentstate == "ENABLED" and self.laseron <> True:
           #if self.cashRFID == rfid:
           #   self.fullname ="Cash"
           #   self.billingRFID = rfid
           #   self.lcd.clear()
           #   self.lcd.message("  Current User  \n      Cash")
           #else :
              self.fullname = ''
	      data = self.authService.GetUserByRFID(rfid)            
              self.fullname = data['FirstName'] + ' ' +data['LastName']
              print(self.fullname)
              self.billingRFID = rfid
              
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
