# -*- coding: utf-8 -*-
""" Air Hockey """

import sys, random
from tkinter import Canvas
from turtle import position
import math
import numpy as np

if sys.version_info.major > 2:
    import tkinter as tk
else:
    import Tkinter as tk

RED, BLACK, WHITE, DARK_RED, BLUE = "red", "black", "white", "dark red", "blue"
ZERO = 5 #for edges.
LOWER, UPPER = "lower", "upper"
HOME, AWAY = "Top", "Bottom"
#Should ALWAYS make a copy of START_SCORE before using it - START_SCORE.copy().
START_SCORE = {HOME: 0, AWAY: 0}
MAX_SCORE = 7 #Winning score.
SPEED = 20 #milliseconds between frame update.
FONT = "ms 50"
MAX_SPEED, PADDLE_SPEED = 15, 15
verbose = True

#### METHODS ####

def str_dict(dic):
    """ Returns a string version of score dictionary - dic """
    return "%s: %d, %s: %d" % (HOME, dic[HOME], AWAY, dic[AWAY])
    
def rand():
    """
    Picks a random tuple to return out of:
    (1, 1), (1, -1), (-1, 1), (-1, -1)
    """
    return random.choice(((1, 1), (1, -1), (-1, 1), (-1, -1))) 
    
#### OBJECT DEFINITIONS ####
        
class Equitment(object):
    """
    Parent class of Puck and Paddle.
    canvas: tk.Canvas object.
    width: int, radius of object.
    position: tuple, initial position (x, y).
    color: string, color of object.
    """
    def __init__(self, canvas, width, position, color):
        self.can, self.w = canvas, width
        self.x, self.y = position
        
        self.Object = self.can.create_oval(self.x-self.w, self.y-self.w, 
                                    self.x+self.w, self.y+self.w, fill=color)
    def update(self, position):
        self.x, self.y = position
        self.can.coords(self.Object, self.x-self.w, self.y-self.w,
                                     self.x+self.w, self.y+self.w)
    def __eq__(self, other):
        overlapping = self.can.find_overlapping(self.x-self.w, self.y-self.w,
                                                self.x+self.w, self.y+self.w)
        return other.get_object() in overlapping
        
    def get_width(self):
        return self.w
    def get_position(self):
        return self.x, self.y
    def get_object(self):
        return self.Object
class TargetManager(Equitment):
    def __init__(self, canvas, width, position):
        Equitment.__init__(self, canvas, width, position, RED)

class PuckManager(Equitment):
    """
    A black instance of Equitment.
    canvas: tk.Canvas object.
    width: int, radius of puck.
    position: tuple, initial position (x, y).
    """
    def __init__(self, canvas, width, position):
        Equitment.__init__(self, canvas, width, position, WHITE)
        
# class Paddle(Equitment):
#     """
#     A red instance of Equitment with an extra drawing (handle).
#     canvas: tk.Canvas object.
#     width: int, radius of paddle.
#     position: tuple, initial position (x, y).
#     """  
#     def __init__(self, canvas, width, position):
#         Equitment.__init__(self, canvas, width, position, RED)
#         self.handle = self.can.create_oval(self.x-self.w/2, self.y-self.w/2,
#                                 self.x+self.w/2, self.y+self.w/2, fill=DARK_RED)
#     def update(self, position):
#         Equitment.update(self, position)
#         self.can.coords(self.handle, self.x-self.w/2, self.y-self.w/2,
#                                    self.x+self.w/2, self.y+self.w/2)
                                   
class Background(object):
    """
    canvas: tk.Canvas object.
    screen: tuple, screen size (w, h).
    goal_h: int, width of the goal.
    """
    def __init__(self, canvas, screen, goal_h):
        self.can, self.goal_h = canvas, goal_h     
        self.w, self.h = screen
        
        self.draw_bg()
    
    def draw_bg(self):
        self.can.config(bg=BLACK, width=self.w, height=self.h)
        #middle circle
        d = self.goal_h/4
        self.can.create_oval(self.w/2-d, self.h/2-d, self.w/2+d, self.h/2+d, 
                                                     fill=BLACK, outline=BLUE)
        self.can.create_line(self.w/2, ZERO, self.w/2, self.h, fill=BLUE)#middle
        self.can.create_line(ZERO, ZERO, self.w, ZERO, fill=BLUE) #left
        self.can.create_line(ZERO, self.h, self.w, self.h, fill=BLUE) #right
        #top
        self.can.create_line(ZERO, ZERO, ZERO, self.h/2-self.goal_h/2, 
                                                                     fill=BLUE)
        self.can.create_line(ZERO, self.h/2+self.goal_h/2, ZERO, self.h, 
                                                                     fill=BLUE)
        #bottom
        self.can.create_line(self.w, ZERO, self.w, self.h/2-self.goal_h/2, 
                                                                     fill=BLUE)
        self.can.create_line(self.w, self.h/2+self.goal_h/2, self.w, self.h, 
                                                                     fill=BLUE)
                                                                     
    def is_position_valid(self, position, width, constraint=None):
        x, y = position
        #if puck is in goal, let it keep going in.
        if constraint == None and self.is_in_goal(position, width):
            return True
        #bounces
        elif (x - width < ZERO or x + width > self.w or 
            y - width < ZERO or y + width > self.h):
            return False
        #elif constraint == LOWER:
            #return y - width > self.h/2
        #elif constraint == UPPER:
            #return y + width < self.h/2
        else:
            return True    

    def is_in_goal(self, position, width):
        x, y = position
        if (x - width <= ZERO and y - width > self.h/2 - self.goal_h/2 and 
                                    y + width < self.h/2 + self.goal_h/2):
            return HOME
        elif (x + width >= self.w and y - width > self.h/2 - self.goal_h/2 and 
                                        y + width < self.h/2 + self.goal_h/2):
            return AWAY
        else:
            return False
            
    def get_screen(self):
        return self.w, self.h   
    def get_goal_h(self):
        return self.goal_h
class Target(object):
    def __init__(self, canvas, background):
        global posx, posy
        self.background = background
        self.screen = self.background.get_screen()
        posx, posy = self.screen[0]/4, self.screen[1]/4
        self.can, self.t = canvas, self.background.get_goal_h()/8
        self.target = TargetManager(canvas, self.t, (posx, posy))
    def interact(self):
        global x, y
        radius = self.t
        if posx + (radius) == x and posy + (radius) == y:
            print ("target aquired")



class Line(object):
    def __init__(self, canvas, background, width, length=300, tracebackAmt=3, color=WHITE, verbose=verbose):
        self.can = canvas
        self.background = background
        self.screenW, self.screenH = self.background.get_screen()
        self.line_length = length
        self.tracebackAmt = tracebackAmt
        self.xinit, self.yinit = 0, 0
        self.xfinal, self.yfinal = 0, 0
        self.deltaX, self.deltaY = 0, 0
        self.slope = 0
        self.line = self.can.create_line(0, 0, 0, 0, fill=color, width=width)
        self.coordList = None

    # Adds the current position of the puck to the coordinate list. Takes care of updating most other things.
    def update(self, puckX, puckY):
        # Create a numpy array containing the last n coordinates of the puck's path.
        # If coordList is not defined, define it as a numpy array with the x and y coordinate of the puck
        if self.coordList is None:
            self.coordList = np.array([[puckX, puckY]])
        # If coordList is defined, append the x and y coordinate of the puck to the end of the array
        else:
            if self.coordList.shape[0] < self.tracebackAmt:
                self.coordList = np.append(self.coordList, [[puckX, puckY]], axis=0)
            # If coordList is full, remove the first row and append the new x and y coordinate of the puck
            else:
                self.coordList = np.delete(self.coordList, 0, 0)
                self.coordList = np.append(self.coordList, [[puckX, puckY]], axis=0)

                # Set the initial coordinates of the line to the current position of the puck
                self.set_init_coords(puckX, puckY)

                # Calculate the slope of the line between the initial coordinates and the current coordinates
                self.calculate_slope(self.coordList[0, 0], self.coordList[0, 1], puckX, puckY)

                # Calculate the final coordinates of the line
                self.calculate_final_coords(puckX, puckY, self.slope)

                # If the final coordinates of the line are outside of the screen, add a bounce line
                if self.yfinal < ZERO:
                    self.get_intersection(ZERO, ZERO, self.screenW, ZERO)

                # Redraw the line
                self.redraw()

    # Set the initial coordinates of the line.
    def set_init_coords(self, x, y):
        self.xinit, self.yinit = x, y

    # Calculate the slope of the line between a previous position and the line's initial coordinates
    def calculate_slope(self, initX, initY, finalX=None, finalY=None):
        if finalX is None:
            finalX = self.xinit
        if finalY is None:
            finalY = self.yinit
        self.deltaX = finalX - initX
        self.deltaY = finalY - initY
        # Avoid division by zero error
        if self.deltaX == 0:
            self.slope = None
        else:
            self.slope = self.deltaY / self.deltaX
        if verbose:
            print(f'[INFO] DeltaX: {self.deltaX} \n'
                  f'[INFO] DeltaY: {self.deltaY} \n'
                  f'[INFO] Slope: {self.slope}')

    # Calculate the final coordinates of the line. Equations were simplified from:
    # x = x0 + (line_length * cos(arctan(slope)))
    # y = y0 + (line_length * sin(arctan(slope)))
    def calculate_final_coords(self, initX, initY, slope):
        if slope is not None:
            if verbose:
                print(f'[INFO] CoordList: {self.coordList}')
            if self.coordList[0][0] < self.coordList[self.tracebackAmt - 1][0]:
                self.xfinal = initX + (self.line_length / math.sqrt(1 + (slope ** 2)))
            elif self.coordList[0][0] > self.coordList[self.tracebackAmt - 1][0]:
                self.xfinal = initX - (self.line_length / math.sqrt(1 + (slope ** 2)))
            if self.coordList[0][1] < self.coordList[self.tracebackAmt - 1][1]:
                self.yfinal = initY + ((self.line_length * slope) / (math.sqrt(1 + (slope ** 2))))
            elif self.coordList[0][1] > self.coordList[self.tracebackAmt - 1][1]:
                self.yfinal = initY - ((self.line_length * slope) / (math.sqrt(1 + (slope ** 2))))

    # def calculate_outside_length(self, slope, initX, initY, finalX, finalY):
    #     if slope is None:
    #         return None
    #     else:

    # Get the intersection point between two lines
    def get_intersection(self, l2x1, l2y1, l2x2, l2y2):
        if (self.xfinal - self.xinit == 0) and (not (l2x2 - l2x1 == 0)):
            self.slope = None
            l2Slope = (l2y2 - l2y1) / (l2x2 - l2x1)
            xIntersect = self.xinit
            yIntersect = (l2Slope * xIntersect) + (l2y1 - (l2x1 * l2Slope))
            yMax = max(self.yinit, self.yfinal)
            yMin = min(self.yinit, self.yfinal)
            if yMin <= yIntersect <= yMax:
                return xIntersect, yIntersect
            else:
                return None
        elif (not (self.xfinal - self.xinit == 0)) and (l2x2 - l2x1 == 0):
            self.slope = (self.yfinal - self.yinit) / (self.xfinal - self.xinit)
            l2Slope = None
            xIntersect = l2x1
            yIntersect = (self.slope * xIntersect) + (self.yinit - (self.xinit * self.slope))
            yMax = max(self.yinit, self.yfinal)
            yMin = min(self.yinit, self.yfinal)
            if yMin <= yIntersect <= yMax:
                return xIntersect, yIntersect
            else:
                return None
        elif (self.xfinal - self.xinit == 0) and (l2x2 - l2x1 == 0):
            self.slope = None
            return None
        else:
            self.slope = (self.yfinal - self.yinit) / (self.xfinal - self.xinit)
            l2Slope = (l2y2 - l2y1) / (l2x2 - l2x1)
            if self.slope == l2Slope:
                return None
            else:
                xIntersect = ((l2y1 - (l2x1 * l2Slope)) - (self.yinit - (self.xinit * self.slope))) / (
                            self.slope - l2Slope)
                yIntersect = (self.slope * xIntersect) + (self.yinit - (self.xinit * self.slope))
                yMax = max(self.yinit, self.yfinal)
                yMin = min(self.yinit, self.yfinal)
                if yMin <= yIntersect <= yMax:
                    return xIntersect, yIntersect
                else:
                    return None

    def get_init_coords(self):
        return self.xinit, self.yinit

    def get_slope(self):
        return self.slope

    def get_final_coords(self):
        return self.xfinal, self.yfinal

    def redraw(self, xInit=None, yInit=None, xFinal=None, yFinal=None):
        if xInit is None:
            xInit = self.xinit
        if yInit is None:
            yInit = self.yinit
        if xFinal is None:
            xFinal = self.xfinal
        if yFinal is None:
            yFinal = self.yfinal
        self.can.coords(self.line, xInit, yInit, xFinal, yFinal)

    # def update(self, xInit, yInit, xfinal=None, yfinal=None, slope=None):
    #     if (xfinal is not None) or (yfinal is not None):
    #         self.xinit, self.yinit, self.xfinal, self.yfinal = xInit, yInit, xfinal, yfinal
    #         self.can.coords(self.line, xInit, yInit, xInit, yInit)
    #     elif slope is not None:
    #         self.slope = slope
    #         self.xinit, self.yinit = xInit, yInit
    #         self.xfinal, self.yfinal = (xInit + (self.slope * self.line_length)), (yInit + (self.slope * self.line_length))
    #         self.can.coords(self.line, xInit, yInit, xfinal, yfinal)
    #
    # def hide(self):
    #     self.can.coords(self.line, 0, 0, 0, 0)
    #
    # def show(self):
    #     self.can.coords(self.line, self.xinit, self.yinit, self.xfinal, self.yfinal)
    #     # self.w = self.background.get_goal_h()/12
    #
    #
    # # Purposefully made to not detect when the line hits left and right walls of playing field
    # def get_border_intersection(self):
    #     # x = ZERO, y = ZERO | y = ZERO | x = w, y = ZERO
    #     # --------------------------------------------------------------
    #     # x = ZERO           |          | x = w
    #     # --------------------------------------------------------------
    #     # x = ZERO, y = w    | y = w    | x = w, y = w
    #     yMin = min(self.yinit, self.yfinal)
    #     yMax = max(self.yinit, self.yfinal)
    #     if yMin < ZERO:
    #         yIntersect = ZERO
    #         if self.slope is not None:
    #             xIntersect = (yIntersect - (self.yinit - (self.xinit * self.slope))) / self.slope
    #             return xIntersect, yIntersect
    #         elif self.slope is None:
    #             xIntersect = self.xinit
    #             return xIntersect, yIntersect
    #     elif yMax > self.screenH:
    #         yIntersect = self.screenH
    #         if self.slope is not None:
    #             xIntersect = (yIntersect - (self.yinit - (self.xinit * self.slope))) / self.slope
    #             return xIntersect, yIntersect
    #         elif self.slope is None:
    #             xIntersect = self.xinit
    #             return xIntersect, yIntersect
    #     else:
    #         return None, None
    #
    # def get_coords(self):
    #     return self.xinit, self.yinit, self.xfinal, self.yfinal
    #
    # def get_init_coords(self):
    #     return self.xinit, self.yinit
    #
    # def get_final_coords(self):
    #     return self.xfinal, self.yfinal
    #
    # def get_length_outside_screen(self):
    #     # Get the x length of the line that is outside of the boundaries of the screen.
    #     if self.xfinal < ZERO:
    #         outsideX = self.xfinal - ZERO
    #     elif self.xfinal > self.screenW:
    #         outsideX = self.xfinal - self.screenW
    #     else:
    #         outsideX = 0
    #
    #     # Get the y length of the line that is outside of the boundaries of the screen.
    #     if self.yfinal < ZERO:
    #         outsideY = self.yfinal - ZERO
    #     elif self.yfinal > self.screenH:
    #         outsideY = self.yfinal - self.screenH
    #     else:
    #         outsideY = 0
    #
    #     return outsideX, outsideY

      
class Puck(object):
    """
    canvas: tk.Canvas object.
    background: Background object.
    """
    def __init__(self, canvas, background):
        self.background = background
        self.screen = self.background.get_screen()
        self.x, self.y = self.screen[0]/2, self.screen[1]/2
        self.can, self.w = canvas, self.background.get_goal_h()/12
        c, d = rand() #generate psuedorandom directions.
        self.vx, self.vy = 4*c, 6*d
        self.a = 1 #friction
        self.cushion = self.w*0.25
        
        self.puck = PuckManager(canvas, self.w, (self.y, self.x))
        
    def update(self):
        global x, y
        #air hockey table - puck never completely stops.
        if self.vx > 0.25: self.vx *= self.a
        if self.vy > 0.25: self.vy *= self.a
        
        x, y = self.x + self.vx, self.y + self.vy
        if not self.background.is_position_valid((x, y), self.w):
            if x - self.w < ZERO or x + self.w > self.screen[0]:
                self.vx *= -1
            if y - self.w < ZERO or y + self.w > self.screen[1]:
                self.vy *= -1
            x, y = self.x+self.vx, self.y+self.vy
            
        self.x, self.y = x, y
        self.puck.update((self.x, self.y))
        self.line1.update(self.x, self.y)

        # if not self.background.is_position_valid(self.line1.get_final_coords(), 0):
        #     xOutside, yOutside = self.line1.get_length_outside_screen()
        #     intersectx, intersecty = self.line1.get_border_intersection()
        #     # if intersectx is not None:
        #     #     self.line2.update(intersectx, intersecty)

    def get_line_coords(self):
        return self.x, self.y, self.slope

    # def hit(self, paddle, moving):
    #     x, y = paddle.get_position()

    #     if moving:        
    #         if (x > self.x - self.cushion and x < self.x + self.cushion or 
    #                                                 abs(self.vx) > MAX_SPEED):
    #             xpower = 1
    #         else:
    #             xpower = 5 if self.vx < 2 else 2
    #         if (y > self.y - self.cushion and y < self.y + self.cushion or 
    #                                                 abs(self.vy) > MAX_SPEED):
    #             ypower = 1
    #         else:
    #             ypower = 5 if self.vy < 2 else 2
    #     else:
    #         xpower, ypower = 1, 1
            
    #     if self.x + self.cushion < x:
    #         xpower *= -1
    #     if self.y + self.cushion < y:
    #         ypower *= -1
        
    #     self.vx = abs(self.vx)*xpower
    #     self.vy = abs(self.vy)*ypower
    
    def __eq__(self, other):
        return other == self.puck
    def in_goal(self):
        return self.background.is_in_goal((self.x, self.y), self.w)

# class Player(object):
#     """
#     master: tk.Tk object.
#     canvas: tk.Canvas object.
#     background: Background object.
#     puck: Puck object.
#     constraint: UPPER or LOWER (can be None).
#     """
#     def __init__(self, master, canvas, background, puck, constraint):
#         self.puck, self.background = puck, background
#         self.constraint, self.v = constraint, PADDLE_SPEED
#         screen = self.background.get_screen()
#         self.x = screen[0]/2
#         self.y = 60 if self.constraint == UPPER else screen[1] - 50

#         self.paddle = Paddle(canvas, self.background.get_goal_h()/7,
#                                                             (self.x, self.y))
#         self.up, self.down, self.left, self.right = False, False, False, False
        
#         if self.constraint == LOWER:
#             master.bind('<Up>', self.MoveUp)
#             master.bind('<Down>', self.MoveDown)
#             master.bind('<KeyRelease-Up>', self.UpRelease)
#             master.bind('<KeyRelease-Down>', self.DownRelease)
#             master.bind('<Right>', self.MoveRight)
#             master.bind('<Left>', self.MoveLeft)
#             master.bind('<KeyRelease-Right>', self.RightRelease)
#             master.bind('<KeyRelease-Left>', self.LeftRelease)
#         else:
#             master.bind('<w>', self.MoveUp)
#             master.bind('<s>', self.MoveDown)
#             master.bind('<KeyRelease-w>', self.UpRelease)
#             master.bind('<KeyRelease-s>', self.DownRelease)
#             master.bind('<d>', self.MoveRight)
#             master.bind('<a>', self.MoveLeft)
#             master.bind('<KeyRelease-d>', self.RightRelease)
#             master.bind('<KeyRelease-a>', self.LeftRelease)
        
#     def update(self):
#         x, y = self.x, self.y
        
#         if self.up: y = self.y - self.v
#         if self.down: y = self.y + self.v
#         if self.left: x = self.x - self.v
#         if self.right: x = self.x + self.v
        
#         if self.background.is_position_valid((x, y), 
#                                       self.paddle.get_width(), self.constraint):
#             self.x, self.y = x, y
#             self.paddle.update((self.x, self.y))
#         if self.puck == self.paddle:
#             moving = any((self.up, self.down, self.left, self.right))
#             self.puck.hit(self.paddle, moving)
    
#     def MoveUp(self, callback=False):
#         self.up = True
#     def MoveDown(self, callback=False):
#         self.down = True
#     def MoveLeft(self, callback=False):
#         self.left = True
#     def MoveRight(self, callback=False):
#         self.right = True
#     def UpRelease(self, callback=False):
#         self.up = False
#     def DownRelease(self, callback=False):
#         self.down = False
#     def LeftRelease(self, callback=False):
#         self.left = False
#     def RightRelease(self, callback=False):
#         self.right = False
        
class Home(object):
    """
    Game Manager.
    master: tk.Tk object.
    screen: tuple, screen size (w, h).
    score: dict.
    """
    def __init__(self, master, screen, score=START_SCORE.copy()):
        self.frame = tk.Frame(master)
        self.frame.pack()
        self.can = tk.Canvas(self.frame)
        self.can.pack()
        #goal width = 1/3 of screen width
        background = Background(self.can, screen, screen[0]*0.33)
        self.puck = Puck(self.can, background)
        self.target = Target(self.can, background)
        #self.p1 = Player(master, self.can, background, self.puck, UPPER)
        #self.p2 = Player(master, self.can, background, self.puck, LOWER)
        
        master.bind("<Return>", self.reset)
        master.bind("<r>", self.reset)
        
        master.title(str_dict(score))
        
        self.master, self.screen, self.score = master, screen, score
        self.update()
        
    def reset(self, callback=False):
        """ <Return> or <r> key. """
        if callback.keycode == 82: #r key resets score.
            self.score = START_SCORE.copy()
        self.frame.destroy()
        self.__init__(self.master, self.screen, self.score)
        
    def update(self):
        self.puck.update()
        self.target.interact()
        #self.p1.update()
        #self.p2.update()
        if not self.puck.in_goal():
            self.frame.after(SPEED, self.update) 
        else:
            winner = HOME if self.puck.in_goal() == AWAY else AWAY
            self.update_score(winner)
            
    def update_score(self, winner):
        self.score[winner] += 1
        self.master.title(str_dict(self.score))
        if self.score[winner] == MAX_SCORE:
            self.frame.bell()
            self.can.create_text(self.screen[0]/2, self.screen[1]/2, font=FONT,
                                                     text="%s wins!" % winner)
            self.score = START_SCORE.copy()
        else:
            self.can.create_text(self.screen[0]/2, self.screen[1]/2, font=FONT,
                                                 text="Point for %s" % winner)
                                                 
def play(screen):
    """ screen: tuple, screen size (w, h). """
    root = tk.Tk()
#    root.state("zoomed")
#    root.resizable(0, 0)
    Home(root, screen)
    #root.eval('tk::PlaceWindow %s center' %root.winfo_pathname(root.winfo_id()))
    root.mainloop()
            
if __name__ == "__main__":
    """ Choose screen size """  
    screen = 1920, 1080
    
    play(screen)