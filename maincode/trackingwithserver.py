from ast import Break
import socket, threading
import random

from collections import deque

from cv2 import VideoCapture, remap
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

global newthread, ballThread

# construct the argument parse and parse the arguments
isQuitting = False

verbose = False

# WARNING: This will enable debug messages inside the CAMERA loop making console very spammy.
frame_verbose = False

# WARNING: This will enable debug messages inside the SOCKET loop making console very spammy.
socket_verbose = False

def parse_args():
    global HOST, PORT, directory, buffer, pts
    global hueL, hueU, satL, satU, valL, valU

    # greenLower = (65, 39, 46)
    # greenUpper = (85, 256, 226)

    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', default="129.21.58.246", help="Host's port\n(Default: 129.21.58.246)")
    parser.add_argument('-p', '--port', type=int, default="9998", help="Host's port\n(Default: 9998)")
    parser.add_argument('-d', '--directory', default="./Images", help="Directory to save images\n(Default: ./Images)")
    parser.add_argument("-b", "--buffer", type=int, default=64, help="Max buffer size\n(Default: 64)")
    parser.add_argument("-hl", "--hueL", type=int, default=65, help="Hue lower bound\n(Default: 65)")
    parser.add_argument("-hu", "--hueU", type=int, default=85, help="Hue upper bound\n(Default: 85)")
    parser.add_argument("-sl", "--satL", type=int, default=39, help="Saturation lower bound\n(Default: 39)")
    parser.add_argument("-su", "--satU", type=int, default=256, help="Saturation upper bound\n(Default: 256)")
    parser.add_argument("-vl", "--valL", type=int, default=46, help="Value lower bound\n(Default: 46)")
    parser.add_argument("-vu", "--valU", type=int, default=226, help="Value upper bound\n(Default: 226)")
    args = parser.parse_args()
    HOST = args.host
    PORT = args.port
    directory = args.directory
    buffer = args.buffer
    pts = deque(maxlen=buffer)
    hueL, hueU, satL, satU, valL, valU = args.hueL, args.hueU, args.satL, args.satU, args.valL, args.valU

def gstreamer_pipeline(capture_width=1920, capture_height=1080, display_width=1920, display_height=1080, framerate=30, flip_method=0):
    pipeParams = \
        f"nvarguscamerasrc ! " \
        f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, format=(string)NV12, framerate={framerate}/1 ! " \
        f"nvvidconv flip-method={flip_method} ! "\
        f"video/x-raw, width={display_width}, height={display_height}, format=(string)BGRx ! " \
        f"videoconvert ! " \
        f"video/x-raw, format=(string)BGR ! " \
        f"appsink"

    if verbose:
        print(f"[INFO] GStreamer pipeline: {pipeParams}")

    return pipeParams

# Load the calibration lookup table csv file remap_lut.csv 
# (this file can be created using the get_fisheye_params.py script)
# Note: 3Darray[OutLayer, yIn, xIn]
#       OutLayer = 0 >> new x coordinate
#       OutLayer = 1 >> new y coordinate
def load_calibraton_map(file_name):
    global remap_lut

    print(f"[INFO] LOADING CALIBRATION LOOKUP TABLE: {file_name}\n" \
        f"[INFO] PLEASE BE PATIENT, THIS CAN TAKE A MOMENT...")
    # Read the csv file and store in 2D array
    remap_lut = np.loadtxt(file_name, delimiter=',', dtype=np.float32)
    
    # Convert the 2D array to 3D array
    remap_lut = np.reshape(remap_lut, (2, int(remap_lut.shape[0]/2), int(remap_lut.shape[1])))

    if verbose:
        print(f"[INFO] Remap LUT shape: {remap_lut.shape}")

# State of the puck
class Puck():
    px = 0.0 
    py = 0.0

    # On initialization, do nothing
    def __init__(self) -> None:
        pass

    # Get the puck's coordinates
    def get(self):
        if socket_verbose:
            print(f"[INFO] Getting puck's coordinates: {self.px}, {self.py}")

        return self.px, self.py

    # Set the puck's coordinates
    def set(self, x, y):
        if socket_verbose:
            print(f"[INFO] Set the puck's coordinates to: {x}, {y}")

        self.px = x
        self.py = y
       
thePuck = Puck()

# Puck tracking
class PuckThread(threading.Thread):
    def __init__(self):
        # initialize the video stream and allow the camera sensor to warmup
        self.cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        # Give the camera some time to warm up
        time.sleep(2.0) 
        # Set the frame dimensions and fps
        self.w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        if self.cap.isOpened():
            print(f'\n--------------------------------------------------\n' \
                  f'Src opened, {self.w}x{self.h} @ {self.fps} fps' \
                  f'\n--------------------------------------------------\n')

        threading.Thread.__init__(self)
        
    # MAKE CLEANUP CODE FOR WHEN THIS THREAD IS KILLED
    def findPuck(self):
        # if theres a signal from the GPIO pin, do X
        global thePuck, isQuitting

        if frame_verbose:
            print(f"[INFO] FINDING PUCK")

        # Define the lower and upper boundaries of the "green" ball in the HSV color space, then 
        # initialize the list of tracked points
        greenLower = (hueL, satL, valL)
        greenUpper = (hueU, satU, valU)

        pts = deque(maxlen=buffer)

        if self.cap.isOpened():
            if frame_verbose:
                print(f"[INFO] CAPTURE IS OPENED")
            # Run while loop until data is no longer being received from the server
            while not isQuitting:
                # Handle keyboard interrupt and errors
                try:
                    # Grab the current frame
                    ret_val, frame = self.cap.read()

                    # Handle the frame from VideoCapture
                    if not ret_val:
                        if verbose:
                            print(f"[INFO] ret_val {ret_val}")
                            print(f"\n[ERROR] NO FRAME READ. EXITING...\n")
                        isQuitting = True
                        break
                    else:
                        if frame_verbose:
                            print(f"[INFO] FRAME READ")

                    # Convert the frame to the HSV color space
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    
                    # Construct a mask for the color "green", then perform a series of dilations 
                    # and erosions to remove any small blobs left in the mask
                    mask = cv2.inRange(hsv, greenLower, greenUpper)
                    mask = cv2.erode(mask, None, iterations=2)
                    mask = cv2.dilate(mask, None, iterations=2)

                    # Find contours in the mask and initialize the current (x, y) center of the ball
                    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    cnts = imutils.grab_contours(cnts)

                    center = None
                    x = 0
                    y = 0

                    # Only proceed if at least one contour was found
                    if len(cnts) > 0:
                        if frame_verbose:
                            print(f"[INFO] {len(cnts)} CONTOURS FOUND")
                        # Find the largest contour in the mask, then use it to compute the minimum 
                        # enclosing circle and centroid
                        maxCnts = max(cnts, key=cv2.contourArea)
                        ((x, y), radius) = cv2.minEnclosingCircle(maxCnts)

                        # Adjust the coordinates to account for the camera's distortion
                        xOut = remap_lut[0, int(y), int(x)]
                        yOut = remap_lut[1, int(y), int(x)]

                        if frame_verbose:
                            print(f"[INFO] Puck coordinates: {xOut}, {yOut}")

                        # If the radius meets the minimum size requirements, then update the center
                        thePuck.set(xOut, yOut)
            
                except KeyboardInterrupt:
                    print(f"[WARN] KEYBOARD INTERRUPT")
                    isQuitting = True
                    break

                except: 
                    isQuitting = True
                    print(f"\n[ERROR] UNABLE TO READ FROM CAMERA\n")
                    break
                
            self.cap.release()
        else:
            print(f'[INFO] TRYING TO RELEASE CAMERA 2.0')

    def run(self):
        # Calls find puck over and over
        while self.findPuck():
            pass
        self.cap.release()

# Establish a connection with the client
class ClientThread(threading.Thread):
    def __init__(self, clientAddress, clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print (f"[INFO] NEW CONNECTION ADDED: {clientAddress}")

    def run(self):
        global thePuck, isQuitting

        print (f"[INFO] CONNECTION FROM: {clientAddress}")
        msg = ''
        
        # Run while loop until data is no longer being received from the client
        while not isQuitting:
            try:
                # Receive the data and decode it
                data = self.csocket.recv(2048)
                msg = data.decode()

                # If the client stops sending data, kill the connection
                if len(msg) == 0:
                    print(f"\n[ERROR] ClientThread.run(): NO DATA RECEIVED\n" \
                        f"CLOSING CONNECTION...\n")
                    isQuitting = True
                    break

                # Get the puck's coordinates and adjust them
                bx, by = thePuck.get()
                rX = (bx) # * 3.72 # * 0.00214 
                rY = (by) # * 3.72 # * 0.00214

                # Put the coordinates into a string with a timestamp
                msg = [time.perf_counter(), rX, rY]
                msg = str(msg)
                if socket_verbose:
                    print(f"[INFO] SENDING TO CLIENT: {msg}")

                # Encode the data
                msg = msg.encode()

                # Send the data to the client
                self.csocket.send(msg)
            
            except KeyboardInterrupt:
                print(f"[WARN] KEYBOARD INTERRUPT")
                isQuitting = True
                # Threads are joined when the program is quitting
                break

            except:
                isQuitting = True
                print(f"\n[ERROR] UNABLE TO READ FROM CLIENT\n")
                break
            
        print (f"[INFO] CLIENT AT {clientAddress} DISCONNECTED.")


parse_args()
load_calibraton_map('./remap_lut.csv')

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
print(f"[INFO] SERVER STARTED @ {HOST}:{PORT}")
print(f"[INFO] WAITING FOR CLIENT REQUEST...")


server.listen(1)
clientsock, clientAddress = server.accept()
newthread = ClientThread(clientAddress, clientsock)
newthread.start()
ballThread = PuckThread()
ballThread.start()

if isQuitting:
    ballThread.join()
    newthread.join()
    server.close()