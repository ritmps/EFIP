import socket, threading
import random
import RPi.GPIO as GPIO
import time
from time import sleep
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN)


#BALL TRACKING
# tracks objects given their hsv color values. 

# import the necessary packages
from collections import deque

from cv2 import VideoCapture
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
# construct the argument parse and parse the arguments





class Ball():
    #State of the ball
    bx = 0.0 
    by = 0.0
    

    def __init__(self) -> None:
        pass

    def get(self):
        return self.bx, self.by

    def set(self, x, y):
        self.bx = x
        self.by = y

class Sensor():
    # state of the sensor
    leftGoal = False
    rightgoal = False

    def __init__(self):
        pass

    def get(self):
       return leftGoal, rightGoal

    def set(self, left, right):
        self.leftGoal = left
        self.rightgoal = right


#global ball        
theBall = Ball()
# global sensor
theSensor = Sensor()

class BallThread(threading.Thread):

    vs = VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

    def __init__(self):
        threading.Thread.__init__(self)
        #initialize camera
        print("Ball Thread initialized")


        print(gstreamer_pipeline(flip_method=0))
        

        #perhaps call color picker.
        
    

    def findBall(self):
        # if theres a signal from the GPIO pin, do X
        
        #find x y of ball
        global theBall
        #call mutator
        theBall.set(random.random(), random.random())
        ret_val, frame = vs.read()
        cv2.imshow("Frame", frame)


        #Ball tracking
    def gstreamer_pipeline(
        # create camera pipeline
        sensor_id=0,
        capture_width=1920,
        capture_height=1080,
        display_width=960,
        display_height=540,
        framerate=30,
        flip_method=0,
    ):
        return (
            "nvarguscamerasrc sensor-id=%d !"
            "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                sensor_id,
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
        )



    
    def run(self):
        #calls find ball over and over
        print("Ball thread go")
        while True:
            self.findBall()
        vs.release()
        cv2.destroyAllWindows()
        
    

class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print ("New connection added: ", clientAddress)
    def run(self):
        global theBall

        print ("Connection from : ", clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''


        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()
            #print ("from client", msg)
            if msg=='bye':
              break

            
            bx, by = theBall.get()

            msg = str(bx) + ',' + str(-by)
            self.csocket.send(bytes(msg,'UTF-8'))
        
        print ("Client at ", clientAddress , " disconnected...")


LOCALHOST = "127.0.0.1"
PORT = 9998
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for client request..")


while True:
    server.listen(1)
    clientsock, clientAddress = server.accept()
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()
    ballThread = BallThread()
    ballThread.start()
