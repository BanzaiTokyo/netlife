#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import uuid
import re
import json
import tornado.websocket
import random
import datetime

from tornado.options import define, options, parse_command_line

define("port", default=443, help="run on the given port", type=int)

class NetLife(tornado.websocket.WebSocketHandler):
    clients = {} #collection of NetLife objects
    cells = {}
    gridW = 7
    gridH = 12
    maxLife = 30
    stepTime = 3 #movie time, seconds
    sendqueue = {}
    gameState = 0 #0 - waiting 3 sec for movie, 1 - collecting results
    playersChanged = True
    timeout = None
    
    def open(self):
        self.id = str(uuid.uuid4())
        self.active = False
        self.dataReceived = True
        self.isNew = True
        self.cells = {}
        self.color = 0
        self.playerID = '0'
        NetLife.clients[self.id] = self
        print 'Life: connected ', self.id
        s = json.dumps({'code':1, 'initial':1, 'players': NetLife.playersList()})
        self.write_message(s)

    def on_message(self, message):
        message = json.loads(message)
        message['code'] = int(message['code'])
        if message['code'] == 1: #player wants to join the game
          self.playerID = message['playerID']
          print 'Life: message from {0}: {1}'.format(self.playerID, message)
          self.color = message['color']
          self.active = True
          self.dataReceived = True
          self.isNew = True
          NetLife.playersChanged = True
          if not NetLife.timeout: #this is the first player
            NetLife.gameStep()
          else:
            print 'has timeout, waiting'
        elif message['code'] == 2: #player exited
          self.playerExited()
        elif message['code'] == 3: #cell tapped
          if NetLife.gameState == 1:
             print 'cells from {0}'.format(self.playerID)
             data = message['data'].split(' ')
             n = len(data)
             if n % 3 == 0:
                for i in range(n//3):
                  cellX = data[i*3]
                  cellY = data[i*3+1]
                  life = data[i*3+2]
                  coord = cellX + ' ' + cellY
                  self.cells[coord] = {'gridX':int(cellX), 'gridY':int(cellY), 'life': min(int(life), NetLife.maxLife)}
             self.dataReceived = True
             NetLife.checkReceivedData()
        else:
          print "unknown code ", message['code']
            
    def on_close(self):
        if hasattr(self, 'id'):
          del NetLife.clients[self.id]
          print 'Life: {0} exited'.format(self.playerID)
          self.playerExited()
        
    def playerExited(self):
        self.cells = {}
        NetLife.playersChanged = True
        if NetLife.gameState == 1:
          NetLife.checkReceivedData()
        else:
          message = {'code':2, 'playerID':self.playerID}
          print 'playerExited:', message
          self.broadcast(message)
    
    def broadcast(self, message, activeOnly=False, comment='', selfToo=False):
        message = json.dumps(message)
        for c in NetLife.clients.itervalues():
          if (not activeOnly or c.active) and (selfToo or c.id <> self.id):
            if comment:
              print comment, c.playerID
            c.write_message(message)
          
    def generateStartingPosition(self):
        b = True
        startX = 0
        startY = 0
        while b:
          startX = random.randint(1, NetLife.gridW-1)
          startY = random.randint(1, NetLife.gridH-1)
          b1 = False
          for p in NetLife.clients.itervalues():
            if not p.active or not len(p.cells): continue
            for c in p.cells:
              if p.cells[c]['gridX'] == startX or p.cells[c]['gridY'] == startY:
                b1 = True
                break
            if b1: break
          if not b1: b = False
        #end of while
        cell = {'gridX':startX, 'gridY':startY, 'life':NetLife.maxLife//2}
        self.cells['{0} {1}'.format(startX, startY)] = cell

    @classmethod
    def playersList(cls):
        players = []
        for p in NetLife.clients.itervalues():
          if not p.active or not len(p.cells):
             print 'inactive or no cells',p
             continue
          print 'cells:',len(p.cells)
          s = []
          for c in p.cells:
            s = s + ['{0} {1} {2}'.format(p.cells[c]['gridX'], p.cells[c]['gridY'], p.cells[c]['life'])]
          print 's=',s
          players = players + [{'playerID': p.playerID, 'color': p.color, 'cells': ' '.join(s)}]
        return players
            
    @classmethod
    def gameStep(cls): #send field data
        sender = None
        for p in NetLife.clients.itervalues():
          if not p.active or not len(p.cells) or p.isNew: continue
          s = []
          cells = {}
          for c in p.cells:
            if p.cells[c]['life'] > 1:
              cells[c] = p.cells[c]
              cells[c]['life'] -= 1
          p.cells = cells
          if not len(p.cells):
            print 'Life: {0} lose'.format(p.playerID)
            p.playerExited()
            p.active = False
          else:
            sender = p
        for p in NetLife.clients.itervalues():
          if p.active and p.isNew:
             NetLife.playersChanged = True
             p.generateStartingPosition()
             p.isNew = False
             sender = p
        if sender:
           message = {'code':4, 'players':NetLife.playersList()}
           sender.broadcast(message, comment='tick', selfToo=True)
           NetLife.gameState = 0
           NetLife.timeout = tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(seconds=NetLife.stepTime), NetLife.collectResults)
        else:
           NetLife.timeout = None
    
    @classmethod
    def collectResults(cls):
        for p in NetLife.clients.itervalues():
          if not p.active or not len(p.cells) or p.isNew: continue
          p.dataReceived = False
          p.write_message('{"code": 3}')
        NetLife.gameState = 1

    @classmethod
    def checkReceivedData(cls):
        if NetLife.gameState == 0: return
        print 'checking data'
        b = True
        hasActive = False
        for p in NetLife.clients.itervalues():
          if p.active:
            hasActive = True
            b = b and p.dataReceived
        if not hasActive:
          print 'remove timeout'
          NetLife.timeout = None
        if b:
          print 'all ok, next step'
          NetLife.gameState = 0
          NetLife.gameStep()
        else:
          print 'incomplete'
            
#=============== websocket ==================

def main():
    global global_message_buffer, app, chatlog, bot

    logging.getLogger("tornado.access").setLevel(logging.WARNING)
    app = tornado.web.Application(
        [
            (r"/life", NetLife),
            ]
    )
    app.listen(options.port)

    NetLife.timeout = tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(seconds=NetLife.stepTime), NetLife.gameStep)
    
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
