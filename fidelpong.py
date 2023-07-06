#==================================================================================
# Fidelpong client
#----------------------
# version 1.0 (by the_duke 26.8.2012):
#					- bar and ball graphics
#
# version 2.0 (by the_duke 03.09.2012):
#					- victory by number of points
#
# version 3.0 (by the_duke 25.10.2012):
#					- splash screen
#
# version 4.0 (by the_duke 25.10.2012):
#					- arrow keys
#					- background music
#
# version 5.0 (by the_duke 8.11.2012):
#					- Solved slowness bug
#					- using "update" for screen insted of Flip (as dual buffer is totally OUT)
#
# version 6.0 (by myipodspain & PROROK)
#					-Spin Works
#
# version 7.0 (by the_duke & Anton)
#					-fixed spin bugs
#
# version 8.0 (by the_duke & Anton 18.7.2013)
#					-Created debug mode
#					-
# version 8.5 (by the_duke 22.8.2013)
#					-fixing the spin bug...
#					-

#======================
_debug_mode = 0
_debug_server = 'localhost'
#_debug_server = '192.168.0.42' #for playing with Sahsha
#_debug_server = '192.168.0.78' #for playing on Anton's server
#_debug_server = '192.168.0.42'
#======================

# import pygame
import pygame
import math
# import network module
from PodSixNet.Connection import connection, ConnectionListener

#=====================music constants==============
# global constants
FREQ = 44100   # same as audio CD
BITSIZE = -16  # unsigned 16 bit
CHANNELS = 2   # 1 == mono, 2 == stereo
BUFFER = 1024  # audio buffer size in no. of samples
FRAMERATE = 30 # how often to check if playback has finished
#==================================================

# init pygame
pygame.init()

	
# class for I/O on network
# this represent the player, too
class Listener(ConnectionListener):
	# init the player
	def __init__(self, host, port):
		self.Connect((host, port))
		
		# set the window
		self.screen = pygame.display.set_mode((800, 640))
		
		# player number. this can be 0 (left player) or 1 (right player)
		self.num = None
		# players' rects
		self.pedal_width = 8
		self.pedal_height = 80
		self.pedal_x = 10
		self.pedal_y = 260
		self.players = (pygame.Rect(10, 260, self.pedal_width, self.pedal_height), pygame.Rect(785, 260, self.pedal_width, self.pedal_height))
		# players movement
		self.movement = [0, 0]

		# radius of the ball
		self.rad = 6
		# ball's rect
		self.ballrect = pygame.Rect(394, 294, 12, 12)

		# True if the server sended the ready message
		self.ready = False
		# True if the game is working
		self.start = False
		
		# may be 'play' 'win' or 'lose'. win and lose will stop the game.
		self.game_status = 'play'
		
		self.jump_F = 0
		self.jump_step = 0
		#self.jump_frames = 40
		self.jump_frames = 100
		#self.spin_frames = 20
		self.spin_frames = 80
		self.jump_offset = 3
		
		# font for writing the scores
		self.font = pygame.font.SysFont('sans,freesans,courier,arial', 18, True)
		# points of the first and second players
		self.points = [0, 0]
	
	# funtion to manage bars movement
	def Network_move(self, data):
		if data['player'] != self.num:
			self.players[data['player']].top = data['top']
	
	# get the player number
	def Network_number(self, data):
		self.num = data['num']

	# get ballpos
	def Network_ballpos(self, data):
		self.ballrect = pygame.Rect(data['pos'], data['size'])
	
	# if the game is ready
	def Network_ready(self, data):
		self.ready = not self.ready
	
	# change players' score
	def Network_points(self, data):
		self.points[0] = data[0]
		self.points[1] = data[1]
	
	# start the game
	def Network_start(self, data):
		self.ready = False
		self.start = True
		
	def Network_victory(self, data):
		if self.num == data['winner']:
			self.game_status = 'win'
		else:
			self.game_status = 'lose'
	
	#lengthening_axis
	def Rotation_v(self, angle, a, b):
		angle = angle%90
		alpha = math.radians(angle)
		v = (a/2*math.tan(alpha)+b/2)*math.cos(alpha)
		v = int(v)
		#print "alpha in v:"+ str(v)
		return v
	
	#shortening_axis
	def Rotation_u(self, angle, a, b):
		angle = angle%90
		alpha = math.radians(angle)
		u = b/2-(a/2*math.tan(alpha)+b/2)*math.sin(alpha)
		u = int(u)
		#print "alpha in u:"+ str(u)
		return u
	
	# mainloop
	def Loop(self):
		while self.game_status == 'play':
			# update connection
			connection.Pump()
			# update the listener
			self.Pump()
			
			# control user input
			for event in pygame.event.get():
				# end the game in necessary
				if event.type == pygame.QUIT:
					exit(0)
				
				# if the game is started
				elif self.start:
				
					# control user keyboard input
					if event.type == pygame.KEYDOWN:
					
						# if up key is pressed move the bar up
						if event.key == pygame.K_UP:
							self.movement[self.num] = -10
						
						# if down key is pressed move the bar down
						elif event.key == pygame.K_DOWN:
							self.movement[self.num] = 10
							
						# if 'j' is pressed move the bar does the spin-jump trick
						elif event.key == pygame.K_j:
							self.bar_spin_jump()
						
					elif event.type == pygame.KEYUP:
						# if key are released stop the movement
						if event.key in (273, 274):
							self.movement[self.num] = 0
			
			# clear the screen
			self.screen.fill((0, 0, 0))
			
			# if game is working
			if self.start:
				n = 0
				# for each player control his movement
				for move in self.movement:
					if self.jump_F == 1 and n == self.num:
							
						if self.players[n].left < 400:
							#rect = pygame.Rect(40,260,8,80)
							move_x_direction = 1
						else :
							move_x_direction = -1
						
						#the frames for moving on the X axis
						elevation_frames_num = (self.jump_frames-self.spin_frames)/2;
						if self.jump_step < elevation_frames_num :
							self.players[n].left += self.jump_offset * move_x_direction 
						
						elif self.jump_step >= (self.jump_frames - elevation_frames_num):
							self.players[n].left += self.jump_offset * -1 * move_x_direction 
							
						if self.jump_step == (self.jump_frames-1):
							self.jump_F = 0
							
							self.jump_step = 0
						else:	
							self.jump_step += 1
						
						connection.Send({'action': 'move_x', 'player': self.num, 'left': self.players[self.num].left})
						
						self.pedal_middle_x = self.players[n].left + self.pedal_width/2
						self.pedal_middle_y = self.players[n].top + self.pedal_height/2
						
					else:
						# if the bar is at the top of the screen
						if self.players[n].top + move < 0:
							self.players[n].top = 0
							# stop the movement
							self.movement[n] = 0
						# if the bar is at the bottom of the screen
						elif self.players[n].bottom + move > 600:
							self.players[n].bottom = 600
							# stop the movement
							self.movement[n] = 0
						else:
							self.players[n].top += move
					
					n += 1
				
				# send to the server information about movement
				connection.Send({'action': 'move', 'player': self.num, 'top': self.players[self.num].top})
				
				# draw objects
				
				# ballpos
				pos = (self.ballrect.left+self.rad, self.ballrect.top+self.rad)
				# draw the ball
				#pygame.draw.circle(self.screen, (255, 255, 255), pos, self.rad)
				self.screen.blit(pygame.image.load("images/ball_1.png"), pos)
	
				# draw the line at the bottom of the screen
				pygame.draw.line(self.screen, (100, 100, 100), (0, 600), (800, 600))
				
				n = 0
				# for each player draw the bar and print the score at the bottom of the screen
				for rect in self.players:
					# draw the bar
					#pygame.draw.rect(self.screen, (255, 255, 255), rect)
					bar_image = pygame.image.load("images/bar_1.png")
					
					#if bar spins
					#print "jump step: "+ str(self.jump_step) + ", spin frames:"+ str(self.spin_frames) +", plus:"+ str((self.jump_step-self.spin_frames)/2)
					if n == self.num and self.jump_F == 1 and self.jump_step > ((self.jump_frames-self.spin_frames)/2) and self.jump_step < ((self.jump_frames+self.spin_frames)/2):
						current_spin_frame = self.jump_step-((self.jump_frames-self.spin_frames)/2)
						#angle= 360/self.spin_frames*current_spin_frame
						#angle = 360%math.ceil((360/self.spin_frames) * current_spin_frame)
						angle = int(round((360/self.spin_frames) * current_spin_frame))
						#todo: how come I can't get this modulo to work?!
						# = 40 * math.cos(angle)
						#dotY = 40 * math.sin(angle)
						bar_image = pygame.transform.rotate(bar_image, -angle)
						
						#todo: compute the bar image movement down and up when spinning, for spinning around center
						#bar_left = cos(angle)
						
						print("angle:"+ str(angle))
						if angle > 360:
							angle = angle-360
							
						
							
						if angle < 90:
							rect.left = self.rect_left_position_for_spin - self.Rotation_v(angle, self.pedal_width, self.pedal_height)
							
							#rect.top -= self.Rotation_u(angle, self.pedal_width, self.pedal_height)
							print("coord: "+ str(rect.left) +","+ str(rect.top))
							print("middle: "+ str(self.pedal_middle_x) +","+ str(self.pedal_middle_y))
							
						if 1:
							a=1
						elif angle > 270: 
							rect.left -= self.Rotation_u(angle, self.pedal_width, self.pedal_height)
							rect.top -= self.Rotation_v(angle, self.pedal_width, self.pedal_height)
						elif angle > 180:
							rect.top += self.Rotation_u(angle, self.pedal_width, self.pedal_height)
							rect.left += self.Rotation_v(angle, self.pedal_width, self.pedal_height)
						elif angle > 90:
							rect.left -= self.Rotation_u(angle, self.pedal_width, self.pedal_height)
							rect.top += self.Rotation_v(angle, self.pedal_width, self.pedal_height)
						else:
							#rect = rect.move(rect.left+self.Rotation_v(angle, rect.width, rect.height), rect.top-self.Rotation_u(angle, rect.width, rect.height))
							rect.left += self.Rotation_v(angle, self.pedal_width, self.pedal_height)
							rect.top -= self.Rotation_u(angle, self.pedal_width, self.pedal_height)
							
						
						#print "coord: "+ str(rect.left) +","+ str(rect.top)
						#print "middle: "+ str(self.pedal_middle_x) +","+ str(self.pedal_middle_y)
							#angle_x_diff= ((rect.width/2)*math.tan(math.radians(360-angle))+rect.height/2)*math.sin(math.radians(360-angle))-rect.width/2
							#print "x_diff "+ str(angle_x_diff)
						#rect.left -
						#rect.top -= (rect.height/2)-math.cos(math.radians(angle))*(math.tan(math.radians(angle))+rect.height/2)
						#if angle < 90:
						#	#print "go down by:" + str((rect.height/2)-((rect.height/2)*math.sin(math.radians(angle))))#str((rect.height/2)-((rect.height/2)*math.cos(angle)))
						#	angle_height_difference = (rect.height/2)-((rect.height/2)*math.sin(math.radians(angle)))
						#	rect.top += angle_height_difference
						#	
						#else :
						#	angle_height_difference = (rect.height/2)*math.cos(math.radians(angle%90))
						#	rect.top -= angle_height_difference
						#
					elif n == self.num: #get ready for a spin - set the location during movements and jumps
						self.rect_left_position_for_spin = rect.left
						self.rect_top_position_for_spin = rect.top
					
					#print(("rect_left_position_for_spin: "+ str(self.rect_left_position_for_spin)))
					self.screen.blit(bar_image, rect)
					
					if n == self.num:
						if n == 0:
							self.screen.blit(self.font.render(str(self.points[n]), True, (0, 255, 0)), (50, 608))
						else:
							self.screen.blit(self.font.render(str(self.points[n]), True, (0, 255, 0)), (750-self.font.size(str(self.points[n]))[0], 608))
					else:
						if n == 0:
							self.screen.blit(self.font.render(str(self.points[n]), True, (255, 0, 0)), (50, 608))
						else:
							self.screen.blit(self.font.render(str(self.points[n]), True, (255, 0, 0)), (750-self.font.size(str(self.points[n]))[0], 608))
	
					n += 1
				
				# update the screen
				pygame.display.update()
			
			# if self.ready is True
			if self.ready:
				# write some text
				#self.screen.blit(self.font.render('Ready', True, (0, 0, 255)), (400-self.font.size('Ready')[0]/2, 290))
				splash_img = pygame.image.load("images/splashscreen.png")
				self.screen.blit(splash_img, (400-(splash_img.get_width()/2), 290-(splash_img.get_height()/2)))
				# update the screen
				pygame.display.update()
				
				#DEBUG: disable music
				#self.play_background_music()
				
			# print 'Waiting for players...'
			elif not self.start:
				# write some text
				self.screen.blit(self.font.render('Waiting for players...', True, (255, 255, 255)), (400-self.font.size('Waiting for players...')[0]/2, 290))
				# update the screen
				pygame.display.update()
				
	
			# wait 25 milliseconds
			pygame.time.wait(25)
			
			if self.game_status != 'play':
				self.end_game_victory()
				
			
		#wait for closing after game end
		while self.game_status != 'play':
			
			for event in pygame.event.get():
				# end the game if necessary
				if event.type == pygame.QUIT:
					exit(0)
		
	#end the game when one side wins
	def end_game_victory(self):
		if self.game_status == 'win':
			end_image = pygame.image.load("images/success.jpg")
		elif self.game_status == 'lose':
			end_image = pygame.image.load("images/loser.jpg")
		else :
			end_image = pygame.image.load("images/bugs.jpg")
		
		self.screen.blit(end_image, (400-(end_image.get_width()/2), 320-(end_image.get_height()/2)))
		#print end_image.get_width()
		#self.screen.blit(end_image, (0,0))
		pygame.display.flip()
		
	def bar_spin_jump(self):
		self.jump_F = 1
		
	def play_background_music(self):
		try:
			pygame.mixer.init(FREQ, BITSIZE, CHANNELS, BUFFER)
		except pygame.error as exc:
			print("Could not initialize sound system: %s" % exc, file=sys.stderr)
			sys.Exit(1)

		music_file = "audio/Big_Gigantic_Fire_It_Up.ogg"
		pygame.mixer.music.load(music_file)
		pygame.mixer.music.play()

if _debug_mode:
	server = _debug_server
else :
	print('Enter the server ip adresse (previously enter on the server script).')
	print('Empty for localhost')
	# ask the server ip adresse
	server = input('server ip: ')

# control if server is empty
if server == '':
	server = 'localhost'

# init the listener
listener = Listener(server, 31500)
# start the mainloop
listener.Loop()



