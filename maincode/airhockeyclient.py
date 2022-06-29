# -*- coding: utf-8 -*-
""" Air Hockey """
from logging import root
import threading
import sys, random
import socket
if sys.version_info.major > 2:
    import tkinter as tk
import time
global thread_running
HOST = "129.21.58.246"  # The server's hostname or IP address
PORT = 9998  # The port used by the server
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
thread_running = True

#### METHODS ####
def recvcoord():
    global xcoordsock, ycoordsock, thread_running
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            while thread_running:
                s.sendall(b"Data received from client!")
                data = s.recv(1024)
                data = data.decode('utf-8')
                data = eval(data)
                xcoordsock = data[1]
                ycoordsock = data[2]

                print(f"Received {xcoordsock}, {ycoordsock}")

                #print(f"Received {data!r}")
                
def on_close():
    global thread_running, thread, root
    thread_running = True
    root.destroy()


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
        
    def update(self, puckx=None, pucky=None):
        global xcoordsock, ycoordsock
        #air hockey table - puck never completely stops.
        #if self.vx > 0.25: self.vx *= self.a
        #if self.vy > 0.25: self.vy *= self.a
        
        # x, y = self.x + self.vx, self.y + self.vy
        # if not self.background.is_position_valid((x, y), self.w):
        #     if x - self.w < ZERO or x + self.w > self.screen[0]:
        #         self.vx *= -1
        #     if y - self.w < ZERO or y + self.w > self.screen[1]:
        #         self.vy *= -1
        #     x, y = self.x+self.vx, self.y+self.vy
        # 
        # -------------------------------------------------------------
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #     s.connect((HOST, PORT))
        #     while True:
        #         try:
        #             s.sendall(b"Data received from client!")
        #             data = s.recv(1024)
        #             data = data.decode('utf-8')
        #             data = eval(data)
        #             xcoord = data[1]
        #             ycoord = data[2]
        #             self.puck.update((xcoord, ycoord))
            

        #             print(f"Received {xcoord}")

        #             #print(f"Received {data!r}")
        #         except KeyboardInterrupt:
        #             break

        # puckx = random.randrange(1, 200, 1)
        # pucky = random.randrange(1, 200, 1)  
        # self.puckx, self.pucky = puckx, pucky
        # self.puck.update((self.puckx, self.pucky))
        self.x, self.y = xcoordsock, ycoordsock
        self.puck.update((self.x, self.y))

 
    
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
        #goal width = 1/3 of screen width
        background = Background(self.can, screen, screen[0]*0.33)
        self.puck = Puck(self.can, background)
       
        
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
    global thread, root
    root = tk.Tk()
#    root.state("zoomed")
#    root.resizable(0, 0)
    thread = threading.Thread(target=recvcoord)
    thread.start()
    time.sleep(3.0)
    Home(root, screen)
    #root.eval('tk::PlaceWindow %s center' %root.winfo_pathname(root.winfo_id()))
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
            
if __name__ == "__main__":
    """ Choose screen size """  
    screen = 1920, 1080
    play(screen)

