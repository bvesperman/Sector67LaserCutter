
class MachineLogic:

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
        
        newest = max(glob.iglob('/home/pi/ImageLog/*.jpg'), key=os.path.getctime)
        print(newest)
        jpgfile = open(newest).read()
   	amount = 0

	try:
           amount = self.authService.AddMachinePayment(int(self.billingRFID),self.jobtime,self.machineID, 'Laser cut time for {0}'.format(self.jobtime),jpgfile)
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
            self.fullname = user
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
