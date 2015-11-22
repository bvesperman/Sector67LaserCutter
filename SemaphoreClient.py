import socket




def SetSemaphore ( Key, Value):
	s = socket.socket()
	host = socket.gethostname()
	port = 12345
	s.connect((host,port))
	print s.recv(1024)
	s.send('Set ' + Key + ' ' + Value)
	s.close()
	
def GetSemaphore ( Key):
	s = socket.socket()
	host = socket.gethostname()
	port = 12345
	s.connect((host,port))
	print s.recv(1024)
	s.send('Get ' + Key)
	result = s.recv(1024)
	s.close
	return result
