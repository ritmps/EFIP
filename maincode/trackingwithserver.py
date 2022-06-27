from ast import Break
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
import keyboard

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
isQuitting = False

verbose = False

# WARNING: This will enable debug messages inside the CAMERA loop making console very spammy.
frame_verbose = False

# WARNING: This will enable debug messages inside the SOCKET loop making console very spammy.
socket_verbose = False

def gstreamer_pipeline(sensor_id=0, capture_width=1920, capture_height=1080, display_width=1920, display_height=1080, framerate=30, flip_method=0):
    pipeParams = \
        f"nvarguscamerasrc sensor-id={sensor_id} ! " \
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, framerate=(fraction){framerate}/1 ! " \
        f"nvvidconv flip-method={flip_method} ! " \
        f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! " \
        f"videoconvert ! " \
        f"video/x-raw, format=(string)BGR ! appsink"

    if verbose:
        print(f"[INFO] GStreamer pipeline: {pipeParams}")

    return pipeParams

class Ball():
    #State of the ball
    bx = 0.0 
    by = 0.0

    def __init__(self) -> None:
        if verbose:
            print("[INFO] Ball() init")
        pass

    def get(self):
        if verbose:
            print(f"[INFO] Ball.get():\n" \
                f"    self.bx: {self.bx}\n" \
                f"    self.by: {self.by}")
        
        return self.bx, self.by

    def set(self, x, y):
        if verbose:
            print(f"[INFO] Ball.set(x={x}, y={y}):\n" \
                f"    self.bx = {x}\n" \
                f"    self.by = {y}")

        self.bx = x
        self.by = y
        
class Sensor():
    # state of the sensor
    leftGoal = 0
    rightGoal = 0

    def __init__(self):
        if verbose:
            print("[INFO] Sensor() init")
        pass

    def get(self):
        if verbose:
            print(f"[INFO] Sensor.get():\n" \
                f"    self.leftGoal: {self.leftGoal}\n" \
                f"    self.rightGoal: {self.rightGoal}")

        return self.leftGoal, self.rightGoal

    def set(self, left, right):
        if verbose:
            print(f"[INFO] Sensor.set(left={left}, right={right}):\n" \
                f"    self.leftGoal = {left}\n" \
                f"    self.rightGoal = {right}")
        self.leftGoal = left
        self.rightgoal = right

# global ball        
theBall = Ball()
theSensor = Sensor()

class BallThread(threading.Thread):
    # Ball tracking
    def __init__(self):
        global vs
        
        if verbose:
            print(f"[INFO] BallThread() init")

        # initialize the video stream and allow the camera sensor to warmup
        vs = VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)

        self.w = vs.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.h = vs.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = vs.get(cv2.CAP_PROP_FPS)

        threading.Thread.__init__(self)
        # initialize camera
        if verbose:
            print(f"[INFO] BallThread.__init__():\n" \
                f"    vs = {vs}\n" \
                f"    self.w = {self.w}\n" \
                f"    self.h = {self.h}\n" \
                f"    self.fps = {self.fps}")
        
        # print(BallThread.gstreamer_pipeline(flip_method=0))
        # perhaps call color picker.
        
# MAKE CLEANUP CODE FOR WHEN THIS THREAD IS KILLED
    def findBall(self):
        # if theres a signal from the GPIO pin, do X
        global theBall
        global isQuitting

        # To flip the image, modify the flip_method parameter (0 and 2 are the most common)
        ap = argparse.ArgumentParser()
        ap.add_argument("-v", "--video", help="path to the (optional) video file")
        ap.add_argument("-b", "--buffer", type=int, default=64, help="max buffer size")
        args = vars(ap.parse_args())

        if verbose:
            print("[INFO] BallThread.findBall():\n" \
                f"    args = {args}")

        # define the lower and upper boundaries of the "green"
        # ball in the HSV color space, then initialize the
        # list of tracked points
        greenLower = (65, 39, 46)
        greenUpper = (85, 256, 226)
        pts = deque(maxlen=args["buffer"])

        if verbose:
            print("[INFO] BallThread.findBall():\n" \
                f"    greenLower = {greenLower}\n" \
                f"    greenUpper = {greenUpper}\n" \
                f"    pts = {pts}")

        if vs.isOpened():
            print(f'\n--------------------------------------------------\n' \
                f'Src opened, {self.w}x{self.h} @ {self.fps} fps' \
                f'\n--------------------------------------------------\n')

            if verbose:
                print(f"[INFO] BallThread.findBall(): WARMING UP CAMERA")
            time.sleep(2.0)
            if verbose:
                print(f"[INFO] BallThread.findBall(): CAMERA WARMED UP")
            
            try:
                if verbose:
                    print(f"[INFO] BallThread.findBall():\n" \
                        f"    isQuitting: {isQuitting}")
                while not isQuitting:
                    # grab the current frame
                    ret_val, frame = vs.read()  # created an error, was frame = vs.read() at first
                    if frame_verbose:
                        if ret_val:
                            print(f"[INFO] BallThread.findBall():\n" \
                                f"    ret_val: {ret_val}")

                    # handle the frame from VideoCapture or VideoStream
                    frame = frame[1] if args.get("video", False) else frame
                    # if we are viewing a video and we did not grab a frame,
                    # then we have reached the end of the video
                    if frame is None:
                        if verbose:
                            print(f"\n[ERROR] BallThread.findBall(): NO FRAME READ\n" \
                                "BREAKING OUT OF VIDEO LOOP...\n")
                        break

                    #print(frame)

                    # resize the frame, blur it, and convert it to the HSV
                    # color space
                    frame = imutils.resize(frame, width=600)
                    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
                    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
                    # construct a mask for the color "green", then perform
                    # a series of dilations and erosions to remove any small
                    # blobs left in the mask
                    mask = cv2.inRange(hsv, greenLower, greenUpper)
                    mask = cv2.erode(mask, None, iterations=2)
                    mask = cv2.dilate(mask, None, iterations=2)
                        # find contours in the mask and initialize the current
                    # (x, y) center of the ball
                    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)
                    cnts = imutils.grab_contours(cnts)

                    if frame_verbose:
                        print(f"[INFO] BallThread.findBall():\n" \
                            f"    cnts = {cnts}")

                    center = None
                    # only proceed if at least one contour was found
                    x = 0
                    y = 0

                    if len(cnts) > 0:
                        if frame_verbose:
                            print(f"[INFO] BallThread.findBall():\n" \
                                f"    len(cnts) > 0")
                        # find the largest contour in the mask, then use
                        # it to compute the minimum enclosing circle and
                        # centroid
                        c = max(cnts, key=cv2.contourArea)
                        ((x, y), radius) = cv2.minEnclosingCircle(c)
                        
                        if frame_verbose:
                            print(f"[INFO] BallThread.findBall(): CALLING theBall.set()")

                        theBall.set(x, y)

                        # print("x coord: ", x, "y coord: ", y)
                        # M = cv2.moments(c)
                        # center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                
                print(f'[INFO] BallThread.findBall(): TRYING TO RELEASE CAMERA 1.0')   
                vs.release()
     
            except: 
                print(f"\n[ERROR] BallThread.findBall(): UNABLE TO READ FROM CAMERA\n")
                
            vs.release()
        else:
            print(f'[INFO] BallThread.findBall(): TRYING TO RELEASE CAMERA 2.0')

        # return true while works return false if doesnt then in the loop terminate the vs when done

    def run(self):
        # calls find ball over and over
        if verbose:
            print(f"[INFO] BallThread.run(): BALL THREAD GO")
        while self.findBall():
            pass
        vs.release()

class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        if verbose:
            print(f"[INFO] ClientThread({clientAddress}, {clientsocket}) init")
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print (f"[INFO] ClientThread().__init__: NEW CONNECTION ADDED: {clientAddress}")

    def run(self):
        global theBall

        print (f"[INFO] ClientThread.run(): CONNECTION FROM: {clientAddress}")
        # self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        msg = ''

        if verbose:
            print(f"[INFO] ClientThread.run():\n" \
                f"    msg = {msg}")
        
        global isQuitting

        if verbose:
            print(f"[INFO] ClientThread.run():\n" \
                f"    isQuitting: {isQuitting}")

        while not isQuitting:
            data = self.csocket.recv(2048)
            msg = data.decode()

            if socket_verbose:
                print(f"[INFO] ClientThread.run():\n" \
                    f"    data = {data}\n" \
                    f"    msg = {msg}")

            # print ("from client", msg)
            # print(len(msg))
            if len(msg) == 0:
                print(f"\n[ERROR] ClientThread.run(): NO DATA RECEIVED\n" \
                    f"CLOSING CONNECTION...\n")
                isQuitting = True
                break

            bx, by = theBall.get()
            rX = (bx - 31.5) # * 0.00214 
            rY = (by - 11.9) # * 0.00214

            msg = [time.perf_counter(), rX, rY]
            msg = str(msg)
            if socket_verbose:
                print(f'[INFO] msg: {msg}\n' \
                    f'[INFO] msg type: {type(msg)}')

            msg = msg.encode()

            # msg = str(time.perf_counter()) + "," + str(rX) + ',' + str(-rY)
            # msg = str(rX)
            # print(str(rX))
            self.csocket.send(msg)
            if verbose:
                print(f"[INFO] ClientThread.run(): Sent {msg}")
            
        print (f"[INFO] ClientThread.run: CLIENT AT {clientAddress} DISCONNECTED.")

LOCALHOST = "129.21.58.246" # "129.21.55.120", "192.168.0.112"
PORT = 9998
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print(f"[INFO] SERVER STARTED @ {LOCALHOST}:{PORT}")
print(f"[INFO] WAITING FOR CLIENT REQUEST...")


server.listen(1)
clientsock, clientAddress = server.accept()
newthread = ClientThread(clientAddress, clientsock)
newthread.start()
ballThread = BallThread()
ballThread.start()


    




    
