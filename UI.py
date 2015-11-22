

import Adafruit_CharLCDPlate
from Adafruit_I2C import Adafruit_I2C
import time 
import SemaphoreClient

lcd = Adafruit_CharLCDPlate.Adafruit_CharLCDPlate()

prev = -1
btn = ((lcd.SELECT, 'Select'),
	(lcd.LEFT  , 'Left'  ),
    (lcd.UP    , 'Up'    ),
    (lcd.DOWN  , 'Down'  ),
    (lcd.RIGHT , 'Right' ))
lcd.begin(16, 2)




lcd.setCursor(15,0)
lcd.message('0')
time.sleep(0.1)
lcd.setCursor(15,0)
lcd.message('-')
time.sleep(0.1) 


if SemaphoreClient.GetSemaphore('LCDRefresh') == True:
	if self.accruingDue > 0.00 :
		lcd.clear()
		lcd.message("Due:$" + "{0:0.2f}".format(
			float(SemaphoreClient.GetSemaphore('AccruingDue'))  + 
			"\n" + SemaphoreClient.GetSemaphore('Fullname')))
	elif SemaphoreClient.GetSemaphore('Machine') == "ENABLED":
		lcd.clear()
		lcd.message("  Current User  \n" + SemaphoreClient.GetSemaphore('Fullname'))
	elif sSemaphoreClient.GetSemaphore('Machine') == "ON":
		lcd.clear() 
		lcd.message("  Please Swipe  \n    RFID Tag   ")
	elif sSemaphoreClient.GetSemaphore('Machine') == "DISABLED":
		lcd.clear() 
		lcd.message("  Please Turn  \n  On Machine ")



	self.LCDRefresh = False

	if self.DebugMode:
		lcd.clear()
		lcd.message("{0}".format(self.rfid) + " {0}".format(self.billingRFID) + "\n{0}".format(io.input(self.LASERPIN)) +" {0}".format(self.laseron))




def CheckButton(self):
	for self.b in self.btn:
		if self.lcd.buttonPressed(self.b[0]):
			if self.b is not self.prev:
				print(self.b[1])

#		    if self.b[1] == "Down":
#                       self.DebugMode = True
#		    if self.b[1] == "Up":                  
#                       self.DebugMode = False
#                       self.LCDRefresh = True

#		    self.prev = self.b
