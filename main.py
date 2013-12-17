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

counter = 0
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

    '''def getstatus(self):
        return self.status

     def setstatus(self, status):
        self.status = status
        return self.status'''

    def updatestatus(self, coordinates, clicks):

        if buttonlist[coordinates].status == "neighbour" and clicks >= 3:
            buttonlist[coordinates].status = "alive"
        return self.status

    def drawstatus(self, coordinates):
        if "live" in buttonlist[coordinates].status:
            buttonlist[coordinates].background_color = [0.5, 2, 0.5, 1]
        if "neighbour" in buttonlist[coordinates].status:
            buttonlist[coordinates].background_color = [0.5, 0.5, 0.5, 1]
        if "dead" in buttonlist[coordinates].status:
            buttonlist[coordinates].background_color = [1, 1, 1, 1]

    def updatefield(self, coordinates):

        count = 0
        t = ast.literal_eval(coordinates)
        c3 = [-1, 0, 1]
        for x in c3:
            for y in c3:
                if x == 0 and y == 0: #exclude point itself
                    continue
                try:
                    if "alive" in buttonlist[str([t[0]+x,t[1]+y])].status: count +=1
                except:
                    pass


        if count >= 1 and buttonlist[coordinates].status == "dead":
            buttonlist[coordinates].status = "neighbour"
        if count >= 1 and buttonlist[coordinates].status == "neighbour":
            buttonlist[coordinates].status = "neighbour"
        if count == 0 and buttonlist[coordinates].status == "neighbour":
            buttonlist[coordinates].status = "dead"
        if count == 0 and buttonlist[coordinates].status == "dead":
            buttonlist[coordinates].status = "dead"

        return self.status


def calculateMove(clickedcells):
    '''

    '''
    print "next step"
    for x in clickedcells.iterkeys():

        buttonlist[x].updatestatus(x, clickedcells[x])

    for x in buttonlist:
        buttonlist[x].updatefield(x)
        buttonlist[x].drawstatus(x)



def callback(instance):
    clickedcells[instance.id] = clickedcells.get(instance.id, 0) + 1


    print('The button %s is being pressed' % instance.id)



class LifeApp(App):
    counter = 0
    buttonID = Button(id = "_" + str(random.randrange(gameColumns*gameRows)))
    def build(self):
        layout = GridLayout(cols=gameColumns, rows = gameRows)
        for i in range(gameRows*gameColumns):

            x = [i%gameColumns, i/gameColumns]

            btn = Cell(text='', id=str(x), status="neighbour")

            buttonlist[btn.id]=btn
            layout.add_widget(btn)
            btn.bind(on_press=callback)
            #fieldState[str(x)] = Cell("neighbour")
        #make a live cell
        buttonlist[str([random.randrange(gameColumns), random.randrange(gameRows)])].status = "alive"

        Clock.schedule_interval(self.randomly, 3)
        return layout

    def randomly(self, dt):
        buttonlist[str([random.randrange(gameColumns), random.randrange(gameRows)])].status = "alive"
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