import socket

s = socket.socket()
host = socket.gethostname()
port = 12345
s.bind((host,port))

s.listen(5)

semaphores = dict([('UI', 'Idle'), ('Machine', 'Idle')
	, ('Database', 'Idle'), ('LCDRefresh', 'False')
	, ('AccruingDue', '0.00'), ('Fullname', 'Blank')])

while True:
		c, addr = s.accept()
		print 'Got a connection form ',addr
		c.send('Thank you for connecting')
		message = c.recv(1024)
		tokens = message.split()
		print(tokens[0])
		print(tokens[1])
		if tokens[0] == 'Set':
			semaphores[tokens[1]] = tokens[2]
		elif tokens[0] == 'Get':
			c.send(semaphores[tokes[1]])
		c.close()
		
