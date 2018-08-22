#!/usr/bin/python
import json
import requests
from suds.client import Client

class SectorAdmin:



    def GetAuthorizedUsers( self, MachineID):

 	#url = "https://www.pinsoft.net/sectorbilling/payments.asmx?wsdl"
	#client = Client(url)
	#data = client.service.GetMachineAuthorizationByMachineIDForPI(MachineID)
        #result = json.loads(data)

        response = requests.get('http://www.sector67.org/blog/api/machine/get_rfids_for_machine/?machine_id={0}'.format(MachineID))

	return response.json()  #result



    def UpdateMachine(self, MachineID):

	myFile = open("/home/pi/sysinfo/ipinfo.txt")

	ipAddress = ""
	macAddress = ""
	
	
	i = 0

	for myLine in myFile:
		if i==1	:
			print()
			ipAddress = myLine[20:35]

			i = i + 1


		if i==0	:
			print()
			macAddress  = myLine[38:60]

			i = i + 1
	print("ipAddress" + ipAddress)
	print("macAddress" + macAddress)
	url = "https://www.pinsoft.net/sectorbilling/payments.asmx?wsdl"
	client = Client(url)
	client.service.UpdateMachine(MachineID, ipAddress, macAddress)



    def AddMachinePayment ( self, RFID, Amount, MachineID, Description, Image):
        print('add machine payment')
        print('http://www.sector67.org/blog/api/machine/log_machine_usage/?machine_id={0}&unit={1}&rfid={2}'.format(MachineID, Amount, RFID))
        response = requests.post('http://www.sector67.org/blog/api/machine/log_machine_usage/?machine_id={0}&unit={1}&rfid={2}'.format(MachineID, Amount, RFID))
 	print('http://www.sector67.org/blog/api/machine/log_machine_usage/?machine_id={0}&unit={1}&rfid={2}'.format(MachineID, Amount, RFID))
        return response.json()["message"]["charge"]
 	#url = "https://www.pinsoft.net/sectorbilling/payments.asmx?wsdl"
	#client = Client(url)
	#data = client.service.AddMachinePayment(RFID,Amount,MachineID, Description, 0)
	#result = json.loads(data)
        #print(data)
	#return result

    def GetUserByRFID(self,RFID):
        response = requests.post('http://www.sector67.org/blog/api/user/get_user_for_rfid/?rfid={0}'.format(RFID))
        if len(response.json()["message"]["display_name"]) != 0 :
           return response.json()["message"]["display_name"]
        else:
	   response.json()["message"]["user_logins"]

 	#url = "https://www.pinsoft.net/sectorbilling/payments.asmx?wsdl"
	#client = Client(url)
	#data = client.service.GetUserByRFIDForPI(RFID)
        #result = json.loads(data)
	#return result
