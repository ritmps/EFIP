import socket, threading
import random

from collections import deque

from cv2 import VideoCapture
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time

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
        

#global ball        
theBall = Ball()


class BallThread(threading.Thread):
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

    def __init__(self):

        global vs 
        vs = VideoCapture(BallThread.gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

        time.sleep(2.0)

        threading.Thread.__init__(self)
        #initialize camera
        print("Ball Thread initialized")


        # print(BallThread.gstreamer_pipeline(flip_method=0))
        

        #perhaps call color picker.
        
    

    def findBall(self):
    
       
        
        #find x y of ball
        global theBall
        #call mutator
        theBall.set(random.random(), random.random())
        ret_val, frame = vs.read()
        """
        frame = imutils.resize(frame, width=600)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, greenLower, greenUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        """

        cv2.imshow("Frame", frame)


      



    
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


LOCALHOST = "129.21.55.120"
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

    

    




    
