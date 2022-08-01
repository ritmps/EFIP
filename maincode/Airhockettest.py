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

    # Draw the background of the playing field.
    def draw_bg(self):
        self.can.config(bg=BLACK, width=self.w, height=self.h)
        # Draw the middle circle
        d = self.goal_h / 4
        self.can.create_oval(
            self.w / 2 - d,
            self.h / 2 - d,
            self.w / 2 + d,
            self.h / 2 + d,
            fill=BLACK,
            outline=BLUE
        )
        # Draw the middle line
        self.can.create_line(
            self.w / 2,
            ZERO,
            self.w / 2,
            self.h,
            fill=BLUE
        )
        # Draw the line on the left
        self.can.create_line(
            ZERO,
            ZERO,
            self.w,
            ZERO,
            fill=RED
        )
        # Draw the line on the right
        self.can.create_line(
            ZERO,
            self.h,
            self.w,
            self.h,
            fill=BLUE
        )
        # Draw the lines on the top
        self.can.create_line(
            ZERO,
            ZERO,
            ZERO,
            self.h / 2 - self.goal_h / 2,
            fill=BLUE
        )
        self.can.create_line(
            ZERO,
            self.h / 2 + self.goal_h / 2,
            ZERO,
            self.h,
            fill=BLUE
        )
        # Draw the lines on the bottom
        self.can.create_line(
            self.w,
            ZERO,
            self.w,
            self.h / 2 - self.goal_h / 2,
            fill=BLUE
        )
        self.can.create_line(
            self.w,
            self.h / 2 + self.goal_h / 2,
            self.w,
            self.h,
            fill=BLUE
        )

    # Check whether the position is inside the playing field.
    def is_position_valid(self, position, width, constraint=None):
        x, y = position
        # If object is outside of the walls, false.
        if ((x - width) < ZERO) or ((x + width) > self.w) or ((y - width) < ZERO) or ((y + width) > self.h):
            return False
        else:
            return True

    # Check whether the position is inside the goal.
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


class Line(object):
    def __init__(self, canvas, background, width, length=300, tracebackAmt=2, color=WHITE):
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

    def update_coordList(self, puckX, puckY):
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

        # Get the initial coordinates of the puck in the coordList array
        puckXInit, puckYInit = self.coordList[0, 0], self.coordList[0, 1]

        # Calculate the slope of the line between the initial coordinates and the current coordinates
        self.deltaX = puckX - puckXInit
        self.deltaY = puckY - puckYInit
        # Avoid division by zero error
        if self.deltaX == 0:
            self.slope = None
        else:
            self.slope = self.deltaY / self.deltaX

        # Redraw the line
        self.slope_redraw()

    def slope_redraw(self, xInit=None, yInit=None, deltaX=None, deltaY= None):
        # If any of the parameters are set, update the line's parameters accordingly
        if xInit is not None:
            self.xinit = xInit
        if yInit is not None:
            self.yinit = yInit
        if deltaX is not None:
            self.deltaX = deltaX
        if deltaY is not None:
            self.deltaY = deltaY

        # Calculate the final coordinates of the line
        self.xfinal = self.xinit + ((self.deltaX / self.tracebackAmt) * self.line_length)
        self.yfinal = self.yinit + ((self.deltaY / self.tracebackAmt) * self.line_length)
        self.can.coords(self.line, self.xinit, self.yinit, self.xfinal, self.yfinal)

    def update(self, xInit, yInit, xfinal=None, yfinal=None, slope=None):
        if (xfinal is not None) or (yfinal is not None):
            self.xinit, self.yinit, self.xfinal, self.yfinal = xInit, yInit, xfinal, yfinal
            self.can.coords(self.line, xInit, yInit, xInit, yInit)
        elif slope is not None:
            self.slope = slope
            self.xinit, self.yinit = xInit, yInit
            self.xfinal, self.yfinal = (xInit + (self.slope * self.line_length)), (yInit + (self.slope * self.line_length))
            self.can.coords(self.line, xInit, yInit, xfinal, yfinal)

    def hide(self):
        self.can.coords(self.line, 0, 0, 0, 0)

    def show(self):
        self.can.coords(self.line, self.xinit, self.yinit, self.xfinal, self.yfinal)
        # self.w = self.background.get_goal_h()/12

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
                xIntersect = ((l2y1 - (l2x1 * l2Slope)) - (self.yinit - (self.xinit * self.slope))) / (self.slope - l2Slope)
                yIntersect = (self.slope * xIntersect) + (self.yinit - (self.xinit * self.slope))
                yMax = max(self.yinit, self.yfinal)
                yMin = min(self.yinit, self.yfinal)
                if yMin <= yIntersect <= yMax:
                    return xIntersect, yIntersect
                else:
                    return None

    # Purposefully made to not detect when the line hits
    def get_border_intersection(self):
        # x = ZERO, y = ZERO | y = ZERO | x = w, y = ZERO
        # --------------------------------------------------------------
        # x = ZERO           |          | x = w
        # --------------------------------------------------------------
        # x = ZERO, y = w    | y = w    | x = w, y = w
        yMin = min(self.yinit, self.yfinal)
        yMax = max(self.yinit, self.yfinal)
        if yMin < ZERO:
            yIntersect = ZERO
            if self.slope is not None:
                xIntersect = (yIntersect - ) / self.slope
        elif self.xfinal > self.screenW:
            xIntersect = self.screenW

        if self.yfinal < ZERO:
            yIntersect = ZERO
        elif self.yfinal > self.screenH:
            yIntersect = self.screenH

        if

    def get_coords(self):
        return self.xinit, self.yinit, self.xfinal, self.yfinal

    def get_init_coords(self):
        return self.xinit, self.yinit

    def get_final_coords(self):
        return self.xfinal, self.yfinal

    def get_length_outside_screen(self):
        # Get the x length of the line that is outside of the boundaries of the screen.
        if self.xfinal < ZERO:
            outsideX = self.xfinal - ZERO
        elif self.xfinal > self.screenW:
            outsideX = self.xfinal - self.screenW
        else:
            outsideX = 0

        # Get the y length of the line that is outside of the boundaries of the screen.
        if self.yfinal < ZERO:
            outsideY = self.yfinal - ZERO
        elif self.yfinal > self.screenH:
            outsideY = self.yfinal - self.screenH
        else:
            outsideY = 0

        return outsideX, outsideY


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
        # self.cushion = self.w * 0.25
        self.slope = 1
        self.line1 = Line(self.can, self.background, self.w * 2)
        self.line2 = Line(self.can, self.background, self.w * 2)
        self.puck = PuckManager(canvas, self.w, (self.y, self.x))
        # Record the last 5 positions of the puck
        self.tracebackAmt = 5
        self.coordList = None

    def update(self):
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
        self.line1.update_coordList(self.x, self.y)

        if background.is_position_valid(line1.get_final_coords(), 0):
            xOutside, yOutside = self.line1.get_length_outside_screen()

        L5 = ([0, self.screen[1]])
        L6 = ([self.screen[0], self.screen[1]])
        R2 = LineIntersection(L3, L4, L5, L6)
        trigsolve2 = (self.w) / (
            math.tan(math.atan((self.x + deltaX * 300 + R2[0]) / (self.y + deltaY * 300 + R2[1]))))

        if R2[0] <= 960 and R2[1] == 540:
            print("Intersection detected:", R2)
            self.line2.update_line((R2[0] - (trigsolve2), R2[1] + (self.w), (self.x + deltaX * 300) - (trigsolve2),
                                    -(self.y + deltaY * 300 + self.w)))

        if deltaX > 0 and deltaY < 0:

            self.line.update_line((last_coordx, last_coordy, self.x + deltaX * 30, self.y + deltaY * 30))
            L1 = ([0, 0])
            L2 = ([self.screen[0], 0])
            L3 = ([last_coordx, last_coordy])
            L4 = ([self.x + deltaX * 30, self.y + deltaY * 30])
            # L3 = ([0,self.screen[1]], [self.screen[0],self.screen[1]])
            # print(L2)

            R = LineIntersection(L1, L2, L3, L4)
            # R2 = lineintersection(L2, L3)
            # figuring out the angle of intersection then the difference between center and edge intersection
            trigsolve = (self.w) / (math.tan(math.atan((self.x + deltaX * 30 - R[0]) / (self.y + deltaY * 30 - R[1]))))
            # trigsolve2 = (self.w) / (math.tan(math.atan((self.x + deltaX * 300 - R2[0])/(self.y + deltaY * 300 - R2[1]))))
            if R[0] <= 960 and R[1] == 0:
                print("Intersection detected:", R)
                self.line2.update_line((R[0] + (trigsolve), R[1] + (self.w), (self.x + deltaX * 300) + (trigsolve),
                                        -(self.y + deltaY * 300 + self.w)))
            # if R2[0] <= 960 and R2[1] == 540:
            #     print ("Intersection detected:", R2)
            #     self.line2.update_line((R2[0]- (trigsolve2), R2[1]+(self.w), (self.x + deltaX * 300) - (trigsolve2), -(self.y + deltaY * 300+self.w)))






        elif deltaX < -.5 and deltaY > 1.5 or deltaX < -.5 and deltaY < -1.5:
            self.line.update_line((0, 0, 0, 0))

        # # #predictive line
        #    self.can.create_line(last_coordx, last_coordy, self.x + deltaX * 500, self.y + deltaY * 500, fill=BLUE, width = 5)
        #    self.can.coords(Line(self, 5, x, y),last_coordx, last_coordy, self.x + slope * 500, self.y + slope * 500, fill=BLUE, width = 5 )
        #    self.can.coords(line, last_coordx, last_coordy, self.x + deltaX * 500, self.y + deltaY * 500)

        # print(mycoordlist)

        # print(last_coordx, self.x, last_coordy, self.y)

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
    # screen = 1920, 1080

    play(screen)
