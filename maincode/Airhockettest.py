# -*- coding: utf-8 -*-
""" Air Hockey """

import sys, random
from tkinter import Canvas
from turtle import position
import math

if sys.version_info.major > 2:
    import tkinter as tk
else:
    import Tkinter as tk

RED, BLACK, WHITE, DARK_RED, BLUE, LIGHT_GREEN = "red", "black", "white", "dark red", "blue", "light green"
ZERO = 5  # for edges.
LOWER, UPPER = "lower", "upper"
HOME, AWAY = "Top", "Bottom"
# Should ALWAYS make a copy of START_SCORE before using it - START_SCORE.copy().
START_SCORE = {HOME: 0, AWAY: 0}
MAX_SCORE = 7  # Winning score.
SPEED = 20  # milliseconds between frame update.
FONT = "ms 50"
MAX_SPEED, PADDLE_SPEED = 15, 15


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

        self.Object = self.can.create_oval(self.x - self.w, self.y - self.w,
                                           self.x + self.w, self.y + self.w, fill=color)

    def update(self, position):
        self.x, self.y = position
        self.can.coords(self.Object, self.x - self.w, self.y - self.w,
                        self.x + self.w, self.y + self.w)

    def __eq__(self, other):
        overlapping = self.can.find_overlapping(self.x - self.w, self.y - self.w,
                                                self.x + self.w, self.y + self.w)
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
        Equitment.__init__(self, canvas, width, position, LIGHT_GREEN)


class Linemanager(object):
    def __init__(self, canvas, width, position):
        self.can, self.line_width = canvas, width
        self.x, self.y = position
        self.object1 = self.can.create_line(0, 0, 0, 0, fill=WHITE, width=self.line_width)

    def update_line(self, position):
        self.x, self.y, x, y = position
        self.can.coords(self.object1, self.x, self.y,
                        x, y)

    def get_width(self):
        return self.line_width

    def get_position(self):
        return self.x, self.y


    def get_object1(self):
        return self.object1


class Line(object):
    def __init__(self, canvas, background):
        self.can = canvas
        self.background = background
        self.screen = self.background.get_screen()

        # self.w = self.background.get_goal_h()/12


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
        # middle circle
        d = self.goal_h / 4
        self.can.create_oval(self.w / 2 - d, self.h / 2 - d, self.w / 2 + d, self.h / 2 + d,
                             fill=BLACK, outline=BLUE)
        self.can.create_line(self.w / 2, ZERO, self.w / 2, self.h, fill=BLUE)  # middle
        self.can.create_line(ZERO, ZERO, self.w, ZERO, fill=RED)  # left
        self.can.create_line(ZERO, self.h, self.w, self.h, fill=BLUE)  # right
        # top
        self.can.create_line(ZERO, ZERO, ZERO, self.h / 2 - self.goal_h / 2,
                             fill=BLUE)
        self.can.create_line(ZERO, self.h / 2 + self.goal_h / 2, ZERO, self.h,
                             fill=BLUE)
        # bottom
        self.can.create_line(self.w, ZERO, self.w, self.h / 2 - self.goal_h / 2,
                             fill=BLUE)
        self.can.create_line(self.w, self.h / 2 + self.goal_h / 2, self.w, self.h,
                             fill=BLUE)

    def is_position_valid(self, position, width, constraint=None):
        x, y = position
        # if puck is in goal, let it keep going in.
        if constraint == None and self.is_in_goal(position, width):
            return True
        # bounces
        elif (x - width < ZERO or x + width > self.w or
              y - width < ZERO or y + width > self.h):
            return False
        # elif constraint == LOWER:
        # return y - width > self.h/2
        # elif constraint == UPPER:
        # return y + width < self.h/2
        else:
            return True

    def is_in_goal(self, position, width):
        x, y = position
        if (x - width <= ZERO and y - width > self.h / 2 - self.goal_h / 2 and
                y + width < self.h / 2 + self.goal_h / 2):
            return HOME
        elif (x + width >= self.w and y - width > self.h / 2 - self.goal_h / 2 and
              y + width < self.h / 2 + self.goal_h / 2):
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
        posx, posy = self.screen[0] / 4, self.screen[1] / 4
        self.can, self.t = canvas, self.background.get_goal_h() / 8
        self.target = TargetManager(canvas, self.t, (posx, posy))

    def interact(self):
        global x, y
        radius = self.t
        if posx + (radius) == x and posy + (radius) == y:
            print("target aquired")


class Puck(object):
    global mycoordlist
    """
    canvas: tk.Canvas object.
    background: Background object.
    """

    def __init__(self, canvas, background):
        self.background = background
        self.screen = self.background.get_screen()
        self.x, self.y = self.screen[0] / 2, self.screen[1] / 2
        self.can, self.w = canvas, self.background.get_goal_h() / 12
        c, d = rand()  # generate psuedorandom directions.
        self.vx, self.vy = 4 * c, 6 * d
        self.a = 1  # friction
        #self.cushion = self.w * 0.25
        self.array_length = 0
        self.slope = 1
        self.line = Linemanager(canvas, self.w * 2, (0, 0))
        self.line2 =Linemanager(canvas, self.w * 2, (0, 0))
        self.puck = PuckManager(canvas, self.w, (self.y, self.x))

    mycoordlist = []


    def update(self):
        global mycoordlist
        global x, y

        # air hockey table - puck never completely stops.
        if self.vx > 0.25: self.vx *= self.a
        if self.vy > 0.25: self.vy *= self.a

        x, y = self.x + self.vx, self.y + self.vy

        if not self.background.is_position_valid((x, y), self.w):
            if x - self.w < ZERO or x + self.w > self.screen[0]:
                self.vx *= -1
            if y - self.w < ZERO or y + self.w > self.screen[1]:
                self.vy *= -1
            x, y = self.x + self.vx, self.y + self.vy
        # y_next = y + stepY
        # x_next = x + stepX

        self.x, self.y = x, y
        self.puck.update((self.x, self.y))

        mycoordlist.append([self.x, self.y])
        self.array_length = len(mycoordlist)
        # print(array_length)

        last_coordx, last_coordy = mycoordlist[self.array_length - 2]

        deltaX = self.x - last_coordx + 0.0001
        deltaY = self.y - last_coordy + 0.0001
        # line = self.can.create_line(0, 0 , 0, 0, fill=BLUE, width = 5)
        slope = deltaX / deltaY

        # root = Linemanager
        # w = Canvas(root, width=200, height=200)
        # w.pack()
        # var = w.create_line(0, 0, 100, 100)
        def line(p1, p2):
            A = (p1[1] - p2[1])
            B = (p2[0] - p1[0])
            C = (p1[0]*p2[1] - p2[0]*p1[1])
            return A, B, -C

        def intersection(L1, L2):
            D  = L1[0] * L2[1] - L1[1] * L2[0]
            Dx = L1[2] * L2[1] - L1[1] * L2[2]
            Dy = L1[0] * L2[2] - L1[2] * L2[0]
            if D != 0:
                x = Dx / D
                y = Dy / D
                return x,y
            else:
                return False


        if deltaX > 0 and deltaY > 0 or deltaX > 0 and deltaY < 0:
            #    w.coords(var, last_coordx, last_coordy, self.x + deltaX * 500, self.y + deltaY * 500, fill=BLUE, width = 5)
            self.line.update_line((last_coordx, last_coordy, self.x + deltaX * 300, self.y + deltaY * 300))
            L1 = line([0,0], [self.screen[0]-self.w,0])
            L2 = line([last_coordx, last_coordy], [self.x + deltaX * 300, self.y + deltaY * 300])
            

            R = intersection(L1, L2)
            # figuring out the angle of intersection then the difference between center and edge intersection
            trigsolve = (self.w) / (math.tan(math.atan((self.x + deltaX * 300 - R[0])/(self.y + deltaY * 300 - R[1]))))
            if R[0] < 960 and R[1] < 540:
                print ("Intersection detected:", R)
                self.line2.update_line((R[0]+ round(trigsolve), R[1]+(self.w), (self.x + deltaX * 300) + (trigsolve), -(self.y + deltaY * 300+self.w)))
            # else:
            #     print ("No single intersection point detected")
                



        
        elif deltaX < -.5 and deltaY > 1.5 or deltaX < -.5 and deltaY < -1.5:
            self.line.update_line((0, 0, 0, 0))

        # # #predictive line
        #    self.can.create_line(last_coordx, last_coordy, self.x + deltaX * 500, self.y + deltaY * 500, fill=BLUE, width = 5)
        #    self.can.coords(Line(self, 5, x, y),last_coordx, last_coordy, self.x + slope * 500, self.y + slope * 500, fill=BLUE, width = 5 )
        #    self.can.coords(line, last_coordx, last_coordy, self.x + deltaX * 500, self.y + deltaY * 500)

        # print(mycoordlist)

        #print(last_coordx, self.x, last_coordy, self.y)

        # print(self.x, self.y)

    def get_line_coords(self):
        return self.x, self.y, self.slope

    def __eq__(self, other):
        return other == self.puck

    def in_goal(self):
        return self.background.is_in_goal((self.x, self.y), self.w)


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
        # goal width = 1/3 of screen width
        background = Background(self.can, screen, screen[0] * 0.33)
        self.puck = Puck(self.can, background)
        self.target = Target(self.can, background)
        self.line = Line(self.can, background)
        # self.p1 = Player(master, self.can, background, self.puck, UPPER)
        # self.p2 = Player(master, self.can, background, self.puck, LOWER)

        master.bind("<Return>", self.reset)
        master.bind("<r>", self.reset)

        master.title(str_dict(score))

        self.master, self.screen, self.score = master, screen, score
        self.update()

    def reset(self, callback=False):
        """ <Return> or <r> key. """
        if callback.keycode == 82:  # r key resets score.
            self.score = START_SCORE.copy()
        self.frame.destroy()
        self.__init__(self.master, self.screen, self.score)

    def update(self):
        self.puck.update()
        self.target.interact()
        # self.p1.update()
        # self.p2.update()
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
            self.can.create_text(self.screen[0] / 2, self.screen[1] / 2, font=FONT,
                                 text="%s wins!" % winner)
            self.score = START_SCORE.copy()
        else:
            self.can.create_text(self.screen[0] / 2, self.screen[1] / 2, font=FONT,
                                 text="Point for %s" % winner)


def play(screen):
    """ screen: tuple, screen size (w, h). """
    root = tk.Tk()
    #    root.state("zoomed")
    #    root.resizable(0, 0)
    Home(root, screen)
    # root.eval('tk::PlaceWindow %s center' %root.winfo_pathname(root.winfo_id()))
    root.mainloop()


if __name__ == "__main__":
    """ Choose screen size """
    screen = 960, 540
    #screen = 1920, 1080

    play(screen)