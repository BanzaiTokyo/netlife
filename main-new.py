from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import *
from kivy.uix.button import Button
from kivy.clock import Clock
import random, ast


gameColumns = 20
gameRows = 15

buttonlist = {}     #key => button id, value => button instance
fieldState = {}     #key => cell coordinates(tuple), value => Cell class instance
clickedcells = {}   #key => button id, value => number of clicks

'''status
    1 = neighbour
    9 = dead
    10+ = live
'''

livecellsnum = 0
count = 0

class Cell(Button):

    def __init__(self, text, id, status):
         super(Button, self).__init__(text=text, id=id)
         self._status = status


    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
         self._status = status


    def updatestatus(self, clicks):

        if self.status == 1 and clicks >= 3:
            self.status = 14
        if self.status >= 10 and clicks > 0:
            self.status = 14
        if self.status >= 10 and clicks == 0:
            self.status -= 1





    def drawstatus(self):
        if self.status == 14:
            self.background_color = [0.5, 2, 0.5, 1]
        if self.status == 13:
            self.background_color = [0.5, 1.8, 0.5, 1]
        if self.status == 12:
            self.background_color = [0.5, 1.5, 0.5, 1]
        if self.status == 11:
            self.background_color = [0.5, 1.2, 0.5, 1]
        if self.status == 10:
            self.background_color = [0.5, 0.9, 0.5, 1]

        if self.status == 1:
            self.background_color = [0.5, 0.5, 0.5, 1]
        if self.status == 9:
            self.background_color = [1, 1, 1, 1]

    def updatefield(self, id):

        count = 0
        t = ast.literal_eval(id)
        c3 = [-1, 0, 1]
        for x in c3:
            for y in c3:
                if x == 0 and y == 0: #exclude point itself
                    continue
                try:
                    if buttonlist[str([t[0]+x,t[1]+y])].status >= 10: count +=1
                except:
                    pass


        if count >= 1 and self.status == 9:
            self.status = 1
        if count == 0 and self.status == 1:
            self.status = 9






def calculateMove(clickedcells):
    '''

    '''
    global livecellsnum
    livecellsnum = 0
    #print "next step"
    for x in clickedcells.iterkeys():
        buttonlist[x].updatestatus(clickedcells[x])

    for x in buttonlist:
        buttonlist[x].updatefield(x)
        buttonlist[x].drawstatus()
        if buttonlist[x].status >= 10: livecellsnum += 1
    print "number of live cells:", livecellsnum


def callback(instance):
    clickedcells[instance.id] = clickedcells.get(instance.id, 0) + 1


    #print('The button %s is being pressed' % instance.id)



class LifeApp(App):
    counter = 0
    def build(self):
        layout = GridLayout(cols=gameColumns, rows = gameRows)
        for i in range(gameRows*gameColumns):
            x = [i%gameColumns, i/gameColumns]
            btn = Cell(text='', id=str(x), status=1)
            buttonlist[btn.id]=btn
            layout.add_widget(btn)
            btn.bind(on_press=callback)

        #make a live cell
        buttonlist[str([random.randrange(gameColumns), random.randrange(gameRows)])].status = 14

        Clock.schedule_interval(self.randomly, 3)
        return layout

    def randomly(self, dt):
        #buttonlist[str([random.randrange(gameColumns), random.randrange(gameRows)])].status = 14
        calculateMove(clickedcells)
        for i in buttonlist.iterkeys():
            clickedcells[i] = 0


#zagorajuschayasya kletka
        '''
        self.counter += 0.1
        buttonlist['[0, 0]'].background_color = [self.counter, self.counter, self.counter, 1]
        '''




if __name__ == '__main__':
    LifeApp().run()