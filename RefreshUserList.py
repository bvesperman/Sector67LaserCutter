

import RFIDDataAccess
import SectorAdminSite


authService = SectorAdminSite.SectorAdmin()
access = RFIDDataAccess.DataAccess()

try:
   #Pull down the current list of authorized users
   data = authService.GetAuthorizedUsers(machine.machineID)
    
   print('adding users to database')
   #Delete Current Cache of Authorized users
   access.DeleteAllAuthorizedUsers()

   #authService.UpdateMachine(machineID)

   #add the users to the cache
   #for user in data:
      #access.InsertAuthorizedUser(user['RFID'],user['ID'],user['FirstName'] + ' ' +user['LastName'])  

   for user in data["message"]:
   #print (user["rfid"])
      access.InsertAuthorizedUser(int(user["rfid"]),0,user["display_name"]) 

except:
#   rebootTime = time.time() + 60
   print ('Exeception');
