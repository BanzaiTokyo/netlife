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

from tornado.options import define, options, parse_command_line

define("port", default=443, help="run on the given port", type=int)

class NetLife(tornado.websocket.WebSocketHandler):
    clients = {}
    cells = {}
    gridW = 10
    gridH = 15
    maxLife = 30
    sendqueue = {}
    
    def open(self):
        self.id = str(uuid.uuid4())
        self.active = False
        self.cells = {}
        self.color = 0
        self.playerID = '0'
        NetLife.clients[self.id] = self
        print 'Life: connected ', self.id
        s = json.dumps({'code':1, 'initial':1, 'players': NetLife.playersList()})
        print 'sending ', s
        self.write_message(s)

    def on_message(self, message):
        message = json.loads(message)
        message['code'] = int(message['code'])
        if message['code'] == 1: #player wants to join the game
          self.playerID = message['playerID']
          print 'Life: message from {0}: {1}'.format(self.playerID, message)
          self.color = message['color']
          self.active = True
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
              if b1: break;
            if not b1: b = False
          #end of while
          cell = {'gridX':startX, 'gridY':startY, 'life':NetLife.maxLife//2}
          self.cells['{0} {1}'.format(startX, startY)] = cell
          message = {'code':1, 'initial':2, 'players':[{'playerID':self.playerID, 'color':self.color, 
                                              'cells':'{0} {1} {2}'.format(cell['gridX'], cell['gridY'], cell['life'])}]}
          print 'message for code 1:', message
          self.write_message(json.dumps(message))
          message['initial'] = 0
          self.broadcast(message, comment='joined')
              
        elif message['code'] == 2: #player exited
          self.playerExited()
        elif message['code'] == 3: #cell tapped
          #print 'tap ', self.playerID, message['tap']
          if message['tap'] in self.cells:
             if self.cells[message['tap']]['life'] < NetLife.maxLife:
               self.cells[message['tap']]['life'] += 1
          else:
             cellX, cellY = message['tap'].split(' ')
             self.cells[message['tap']] = {'gridX':cellX, 'gridY':cellY, 'life':NetLife.maxLife//2}
          if self.playerID in NetLife.sendqueue:
             NetLife.sendqueue[self.id] = NetLife.sendqueue[self.id] | set([message['tap']])
          else:
             NetLife.sendqueue[self.id] = set([message['tap']])
        else:
          print "unknown code ", message['code']
            
    def on_close(self):
        if hasattr(self, 'id'):
          del NetLife.clients[self.id]
          print 'Life: {0} exited'.format(self.playerID)
          self.playerExited()
        
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
         
    def broadcast(self, message, activeOnly=False, comment='', selfToo=False):
        message = json.dumps(message)
        for c in NetLife.clients.itervalues():
          if (not activeOnly or c.active) and (selfToo or c.id <> self.id):
            if comment:
              print comment, c.playerID
            c.write_message(message)
          
            
    def playerExited(self):
        message = {'code':2, 'playerID':self.playerID}
        print 'Player exited:', message
        self.broadcast(message)
    
    @classmethod
    def gameStep(cls):
        sender = None
        for p in NetLife.clients.itervalues():
          sender = p
          if not p.active or not len(p.cells): continue
          s = []
          cells = {}
          for c in p.cells:
            if p.cells[c]['life'] > 0:
              cells[c] = p.cells[c]
              cells[c]['life'] -= 1
          p.cells = cells
          if not len(p.cells):
            print 'Life: {0} lose'.format(p.playerID)
            p.playerExited()
            p.active = False
        if sender:
           message = {'code':4}
           sender.broadcast(message, comment='tick', selfToo=True)
    
    @classmethod
    def sendertick(cls):
        message = []
        sender = None
        for cl in NetLife.sendqueue:
          if NetLife.clients[cl]:
            p = sender = NetLife.clients[cl]
            print 'sq=',NetLife.sendqueue[cl]
            for c in NetLife.sendqueue[cl]:
              print 'c=',c
              message = message + [{'tap': p.playerID+' '+c+' '+str(p.cells[c]['life'])}]
        if len(message):
           message = {'code':3, 'taps':message}
           sender.broadcast(message, comment='tap ', selfToo=True)
        NetLife.sendqueue = {}
            
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

    tornado.ioloop.PeriodicCallback(NetLife.gameStep, 1000).start()
    tornado.ioloop.PeriodicCallback(NetLife.sendertick, 300).start()
    
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
