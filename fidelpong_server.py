# Excuse me for the my bad English, I hope you can understand my comments
# pygame site: www.pygame.org
#
#==================================================================================
# Fidelpong server
#----------------------
# version 1.0 (by the_duke 26.8.2012):
#					- faster ball
#
# version 2.0 (by the_duke 03.09.2012):
#					- victory by number of points
#
# version 2.1 (by the_duke 03.09.2012):
#					- bugfix: server death before "victory" is sent. (occurs on slow connections).
#
# version 2.2 (by the_duke 22.11.2012):
#					- bugfix: 
#
# version 2.3 (by the_duke & Anton 18.7.2013)
#					-Created debug mode

#======================
_debug_mode = 1
_debug_server = 'localhost'
#_debug_server = '192.168.0.42' #for playing with Anton
#======================

# import pygame
import pygame
# import network modules
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
# random module to randomize the initial ball direction
from random import randint

# function which return a random value between -1 and -3
# or between 1 and 3
# this in userful for set the initial ball direction
def speed():
	# randomize the sign
	if randint(1, 2) == 1:
		sign = -1
	else:
		sign = 1
	
	# return the value
	return sign*6

# class representing a sigle connection with a client
# this can also represent a player
class ClientChannel(Channel):
	def __init__(self, *args, **kwargs):
		Channel.__init__(self, *args, **kwargs)
		
		# points of the player
		self.points = 0
		# rect of the player's bar
		self.rect = None
	
	# function called when a player begin a movement
	def Network_move(self, data):
		self.rect.top = data['top']
		# send to all other clients the information about moving
		self._server.SendToAll(data)
		
	def Network_move_x(self, data):
		self.rect.left = data['left']
		# send to all other clients the information about moving
		self._server.SendToAll(data)

# class representing the server
class MyServer(Server):
	channelClass = ClientChannel
	
	# Start the server
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		
		# ball's speeds on x and y axis
		self.ballspeed = {'x': speed(), 'y':speed()}
		# rect that contain the ball
		self.ballrect = pygame.Rect(394, 294, 12, 12)
		# radious of the ball
		self.rad = 6
		
		# if self.start is True the game is working 
		self.start = False
		# time before strating the game in milliseconds
		self.wait_to_start = -1
		
		# rects of the players' bars
		self.rects = (pygame.Rect(10, 260, 8, 80), pygame.Rect(785, 260, 8, 80))
		# players
		self.players = []
		
		#points for winning
		#self.points_to_win = 100;
		#for debug:
		self.points_to_win = 10000;
		
		# adresse and port at which server is started
		adresse, port = kwargs['localaddr']
		
		print 'Server started at', adresse, 'at port', str(port)
		print 'Now you can start the clients'
	
	# function called on every connection
	def Connected(self, player, addr):
		print 'Player connected at', addr[0], 'at port', addr[1]
		
		# add player to the list
		self.players.append(player)
		# set the bar rect of the player
		player.rect = self.rects[len(self.players)-1]
		# send to the player his number
		player.Send({'action': 'number', 'num': len(self.players)-1})
		# send the initial ball speed
		player.Send({'action': 'ballspeed', 'x': self.ballspeed['x'], 'y': self.ballspeed['y']})
		
		# if there are two player we can start the game
		if len(self.players) == 2:
			# send to all players the ready message
			self.SendToAll({'action': 'ready'})
			# wait 4 seconds before starting the game
			self.wait_to_start = 3000
	
	# this send to all clients the same data
	def SendToAll(self, data):
		[p.Send(data) for p in self.players]
	
	def Loop(self):
		keep_playing_F = True
	
		# infinite loop
		while keep_playing_F:
			# update server connection
			myserver.Pump()
			
			# if the game is started
			if self.start:
				# for each player
				for player in self.players:
					# control if the bar and the ball are colliding
					if player.rect.colliderect(self.ballrect):
						# invert the ball speed
						self.ballspeed['x'] = -self.ballspeed['x']
						# add a point if the player touch the ball
						player.points += 1
						# send point to the clients
						self.SendToAll({'action': 'points', 0: self.players[0].points, 1: self.players[1].points})
				
				# move the ball
				self.ballrect.left += self.ballspeed['x']
				self.ballrect.top += self.ballspeed['y']
				
				# if the ball touch the top or bottom side change the ball speed
				if self.ballrect.top <= 0:
					self.ballspeed['y'] = -self.ballspeed['y']
				elif self.ballrect.bottom >= 600:
					self.ballspeed['y'] = -self.ballspeed['y']
				
				#flags whether points were raised for a player
				self.points_raised_F = False
				# if the ball touch the left ot right side reset the ball position
				if self.ballrect.left <= 0:
					# reset the ball position
					self.ballrect = pygame.Rect(394, 294, 12, 12)
					# add point to player two
					self.players[1].points += 10
					# send point to the clients
					self.SendToAll({'action': 'points', 0: self.players[0].points, 1: self.players[1].points})
					self.points_raised_F = True
					
				elif self.ballrect.right >= 800:
					# reset the ball position
					self.ballrect = pygame.Rect(394, 294, 12, 12)
					# add point to player one
					self.players[0].points += 10
					# send point to the clients
					self.SendToAll({'action': 'points', 0: self.channels[0].points, 1: self.channels[1].points})
					self.points_raised_F = True
				
				#announce victory if needed
				if self.points_raised_F:
					if self.players[0].points >= self.points_to_win:
						self.SendToAll({'action': 'victory', 'winner': 0})
						myserver.Pump()
						keep_playing_F = False
						pygame.time.wait(3000)
					elif self.players[1].points >= self.points_to_win:
						self.SendToAll({'action': 'victory', 'winner': 1})
						myserver.Pump()
						keep_playing_F = False
						pygame.time.wait(3000)
					else:
						self.points_raised_F = False
					
					
				# send the ball rect
				self.SendToAll({'action': 'ballpos', 'pos': self.ballrect.topleft, 'size': self.ballrect.size})
			
			# wait 25 milliseconds
			pygame.time.wait(25)
			
			# reduce wait to start time if necessary
			if self.wait_to_start > 0:
				self.wait_to_start -= 25
			# if time = 0 start the game
			elif self.wait_to_start == 0:
				self.start = True
				self.wait_to_start = -1
				# send to all player the start message
				self.SendToAll({'action': 'start'})
				
		#waiting for the ending pictures to show up before killing server
		pygame.time.wait(200)

if _debug_mode:
	adresse = _debug_server
else :
	print 'Enter the ip adresse of the server. Normally the ip adresse of the computer.'
	print 'example: localhost or 192.168.0.2'
	print 'Empty for localhost'
	# ip adresse of the server (normally the ip adresse of the computer)
	adresse = raw_input('Server ip: ')

# control if adresse is empty
if adresse == '':
	adresse = 'localhost'

# inizialize the server
myserver = MyServer(localaddr=(adresse, 31500))
# start mainloop
myserver.Loop()
