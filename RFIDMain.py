import requests
import json
import datetime
import RFIDDataAccess
import SectorAdminSite
import sys
import time 
import datetime 
import RPi.GPIO as io 
import select
from time import gmtime, strftime
import subprocess
import os
import MachineLogic


localRFID = ""
rebootTime = time.time() + 86400

machine = MachineLogic.MachineLogic()
machine.Setup()

authService = SectorAdminSite.SectorAdmin()
access = RFIDDataAccess.DataAccess()

try:
   #Pull down the current list of authorized users
   data = authService.GetAuthorizedUsers(machine.machineID)

   #Delete Current Cache of Authorized users
   access.DeleteAllAuthorizedUsers()

   #authService.UpdateMachine(machineID)

   #add the users to the cache
   for user in data:
      access.InsertAuthorizedUser(user['RFID'],user['ID'],user['FirstName'] + ' ' +user['LastName'])  

except:
   rebootTime = time.time() + 60
   print ('Exeception');
  

#loop forever
while True:

    # read the standard input to see if the RFID has been swiped
    while sys.stdin in select.select([sys.stdin],[],[],0)[0]:
        localRFID = sys.stdin.readline()
        if localRFID:
            localRFID = ''.join(localRFID.splitlines())

            #RFID has been swiped now check if authorized
	    print(int(localRFID))    	    
            if access.IsRFIDAuthorized(int(localRFID)):
	       machine.rfid = int(localRFID)
	       machine.DoAuthorizedWork()

            else:
               machine.SetBillingAccount(int(localRFID))

    machine.DoUnAuthorizedContinuousWork()
    #machine.CheckBeam()


    time.sleep(.0001)

    if  time.time() > rebootTime and not machine.Busy():
        print("rebooting")
        os.system("reboot")


