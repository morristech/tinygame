
from panda3d.core import PandaNode,NodePath
import random
from sprite import Sprite2d

class NetObj:
	def getState(self):
		return {'type':self.__class__.id}

class NetEnt(NetObj):
	entities = {}
	currentID = 1
	types = {}
	def __init__(self, id=None):
		if not id:
			print 'CREATING (id not asserted)'
			id = NetEnt.currentID
			NetEnt.currentID += 1
		self.id = id
		
		print 'CREATING: Entities[',self.id,'] = ',self,'type=',self.__class__
		
		assert self.id not in NetEnt.entities
		NetEnt.entities[self.id] = self
	@staticmethod
	def registerSubclass(classval):
		classval.id = len(NetEnt.types)
		NetEnt.types[classval.id] = classval
	@staticmethod
	def getState():
		d = {}
		for id, ent in NetEnt.entities.iteritems():
			#print 'getting state of ent',id,' ',ent
			d[id] = ent.getState()
		return d
	@staticmethod
	def setState(stateDict):
		# first pass at state data: allocate missing entities
		for id, entState in stateDict.iteritems():
			if isinstance(entState, dict):
				if id not in NetEnt.entities:
					print 'creating ent with id',id,'of type',NetEnt.types[entState['type']]
					e = NetEnt.types[entState['type']](id=id)

		# apply state in second pass to allow for entity assignment
		for id, entState in stateDict.iteritems():
			if isinstance(entState, dict):
				NetEnt.entities[id].setState(entState)

class NetPool(NetEnt):
	def __init__(self, id=None):
		NetEnt.__init__(self, id)
		self.pool = set()
	def getState(self):
		return list(self.pool)
	def setState(self, newPool):
		self.pool = set(newPool)
	def add(self, ent):
		self.pool.add(ent.id)
	def remove(self, ent):
		self.pool.remove(ent.id)
	def values(self):
		return [NetEnt.entities[i] for i in self.pool]
NetEnt.registerSubclass(NetPool)

## simple usage below
class NetNodePath(NodePath):
	def __init__(self, node):
		NodePath.__init__(self, node)
		self.rotationallyImmune = False
	def getState(self):
		pos = self.getPos()
		return [str(self.getParent()),(pos[0],pos[1],pos[2]),self.getH()]
	def setState(self, data):
		par,pos,h = data
		#self.setParent(par) #todo: fix
		self.setPos(pos[0],pos[1],pos[2])
		if not self.rotationallyImmune:
			self.setH(h)

CharacterPool = NetPool()
class Character(NetEnt):
	startPosition = None
	def __init__(self, id=None):
		NetEnt.__init__(self, id)
		self.node = NetNodePath(PandaNode("A Character"))
		self.node.setPos(Character.startPosition)
		self.node.reparentTo(render)
		CharacterPool.add(self)
		
		self.sprite = Sprite2d("origsprite.png", rows=3, cols=5, anchorX=Sprite2d.ALIGN_CENTER, rowPerFace=(0,1,2,1))
		self.sprite.createAnim("walk",(1,0,2,0))
		self.sprite.node.reparentTo(self.node)

	def getState(self):
		dataDict = NetObj.getState(self)
		dataDict[0] = self.node.getState()
		return dataDict
	def setState(self, dataDict):
		x,y = self.node.getX(), self.node.getY()
		self.node.setState(dataDict[0])
		self.animate(self.node.getX()-x, self.node.getY()-y)
	def animate(self, deltaX, deltaY):
		if deltaX or deltaY:
			self.sprite.playAnim("walk", loop=True)
		else:
			self.sprite.setFrame(0)
NetEnt.registerSubclass(Character)

UserPool = NetPool()
class User(NetEnt):
	def __init__(self, id=None, address=None, remoteAck=None, localAck=None):
		NetEnt.__init__(self, id)
		self.points = 0
		if address:
			self.address = address
			self.remoteAck = remoteAck # most recent message they've acked
			self.localAck = localAck   # most recent message from them I've acked
		self.last = None
		if not id:
			#don't create sub-item, will be passed from server.
			self.char = Character()
		UserPool.add(self)
	def getState(self):
		dataDict = NetObj.getState(self)
		try:
			dataDict[0] = self.char.id
		except AttributeError:
			dataDict[0] = None
		dataDict[1] = self.points
		return dataDict
	def setState(self, dataDict):
		self.char = NetEnt.entities[dataDict[0]]
		self.points = dataDict[1]
NetEnt.registerSubclass(User)

import rencode
if __name__ == '__main__':
	#common
	chars = NetPool()
	
	#client
	state = {1:[2,3], 2:{'type':1, 0:('(empty)',[0.1,0.2,0.3]), 1:'charname'}}
	strstate = rencode.dumps(state)
	print len(strstate)
	print strstate
	state = rencode.loads(strstate)
	NetEnt.setState(state)
	
	#server
	#for i in range(10):
	#	chars.add(Character())
	print NetEnt.entities
	print NetEnt.types
	x = NetEnt.getState()

	print len(rencode.dumps(x))
	print x