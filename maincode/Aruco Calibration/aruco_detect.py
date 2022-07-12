import argparse
import time
import imutils
import cv2
import numpy as np
import sys

global HOST, PORT, lutPath, directory, tag_type

verbose = True
timings = True

ARUCO_DICT = {
	"DICT_4X4_50": cv2.aruco.DICT_4X4_50,
	"DICT_4X4_100": cv2.aruco.DICT_4X4_100,
	"DICT_4X4_250": cv2.aruco.DICT_4X4_250,
	"DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
	"DICT_5X5_50": cv2.aruco.DICT_5X5_50,
	"DICT_5X5_100": cv2.aruco.DICT_5X5_100,
	"DICT_5X5_250": cv2.aruco.DICT_5X5_250,
	"DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
	"DICT_6X6_50": cv2.aruco.DICT_6X6_50,
	"DICT_6X6_100": cv2.aruco.DICT_6X6_100,
	"DICT_6X6_250": cv2.aruco.DICT_6X6_250,
	"DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
	"DICT_7X7_50": cv2.aruco.DICT_7X7_50,
	"DICT_7X7_100": cv2.aruco.DICT_7X7_100,
	"DICT_7X7_250": cv2.aruco.DICT_7X7_250,
	"DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
	"DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
	"DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
	"DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
	"DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
	"DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11
}

class timer:
    global verbose, timings
    
    def __init__(self):
        self.avg = 0
        self.count = 0
        self.start = 0
        self.curDuration = 0
    
    def start_timer(self, action: str = None):
        self.start = time.time()
        if action is ((not None) and (verbose)):
                print(f'[INFO] {action.upper()} STARTED')

    def update(self, action: str):
        if verbose or timings:
            self.curDuration = (time.time() - self.start) * 1000
            if verbose:
                print(f'[INFO] {action.upper()} TOOK {self.curDuration}ms')
            if timings:
                self.update_average()

    def update_average(self):
        self.count += 1
        self.avg = self.avg + ((self.curDuration - self.avg) / self.count)
        self.start_timer()

    def get_average(self):
        return self.avg
    
    def get_curDuration(self):
        return self.curDuration

lutTime = timer()
avgUndistTime = timer()
avgDetectTime = timer()

def args_parse():
    global HOST, PORT, lutPath, directory, tag_type
    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', type=str, default="0.0.0.0", help="Host's port\n    (Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', type=int, default=5004, help="Host's port\n    (Default: 5004)")
    parser.add_argument('-l', '--lookup', type=str, default="../remap_lut.csv", help="Path to lookup table\n    (Default: /workspaces/EFIP/maincode/remap_lut.csv)")
    parser.add_argument('-d', '--directory', type=str, default="Tags", help="Directory to ArUCo tags\n    (Default: Tags)")
    parser.add_argument('-t', '--type', type=str, default="DICT_5X5_100", help="Type of ArUCo tag to detect\n    (Default: DICT_5X5_100)")
    args = parser.parse_args()
    HOST = args.host
    PORT = args.port
    lutPath = args.lookup
    directory = args.directory
    tag_type = ARUCO_DICT[args.type]
    print(f'Host: {HOST}\nPort: {PORT}')

def gstreamer_in(width=1920, height=1080, fps=60):
    pipeinParams = \
        f"nvarguscamerasrc ! " \
        f"video/x-raw(memory:NVMM), width={width}, height={height}, format=(string)NV12, framerate={fps}/1 ! " \
        f"nvvidconv flip-method=0 ! "\
        f"video/x-raw, width=1920, height=1080, format=(string)BGRx ! " \
        f"videoconvert ! " \
        f"video/x-raw, format=(string)BGR ! " \
        f"appsink"
    return (pipeinParams)

# Define the output stream for gstreamer
def gstreamer_out(host, port):
    pipeoutParams = \
        f"appsrc ! " \
        f"video/x-raw, format=BGR ! " \
        f"queue ! " \
        f"videoconvert ! " \
        f"video/x-raw,format=BGRx ! " \
        f"nvvidconv ! " \
        f"nvv4l2h264enc ! " \
        f"h264parse ! " \
        f"rtph264pay pt=96 config-interval=1 ! " \
        f"udpsink host={host} port={port}"
    return (pipeoutParams)

def getDistortLUT():
    global lutTime
    lutTime.start_timer()
    
    print(f"[INFO] LOADING CALIBRATION LOOKUP TABLE: {lutPath}\n" \
        f"[INFO] PLEASE BE PATIENT, THIS CAN TAKE A MOMENT...")

    # Read the csv file and store in 2D array
    remap_lut = np.loadtxt(lutPath, delimiter=',', dtype=np.float32)
    
    # Split the array into mapx and mapy
    mapx, mapy = np.vsplit(remap_lut, 2)

    lutTime.update('loading calibration lookup table')
    return (mapx, mapy)

# Function to undistort the image using the look up table
def undistort_img(image, lutmapx, lutmapy):
    global avgUndistTime
    avgUndistTime.start_timer('undistorting image')
    
    # Undistort the image using the look up table
    undist = cv2.remap(image, lutmapx, lutmapy, cv2.INTER_LINEAR)

    avgUndistTime.update('undistorting image')
    return undist

def detect_aruco(image):
    global avgDetectTime
    avgDetectTime.start_timer('detecting aruco tags')
	
    # detect aruco tags
    parameters = cv2.aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, tag_type, parameters=parameters)
    
    avgDetectTime.update('detecting aruco tags')
    return corners, ids, rejectedImgPoints

# Returns corners, ids, rejected image points, and marks up an image using the detected points
def detect_aruco_markup(image):
    global avgDetectTime
    avgDetectTime.start_timer('detecting aruco tags')
    
    # detect aruco tags
    parameters = cv2.aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, tag_type, parameters=parameters)
    # draw aruco tags
    image = cv2.aruco.drawDetectedMarkers(image, corners, ids)

    avgDetectTime.update('detecting aruco tags')
    return image, corners, ids, rejectedImgPoints

def read_cam():
    global img, stop_thread

    # First iteration of the while loop = true
    firstloop = True

    # Stop any running threads = false
    stop_thread = False

    # Read Gstreamer pipeline into OpenCV (pipein)
    cap = cv2.VideoCapture(gstreamer_in(), cv2.CAP_GSTREAMER)

    # Get the width, height and fps of the stream and print it to the console
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f'\n--------------------------------------------------\n' \
          f'Src opened, {w}x{h} @ {fps} fps' \
          f'\n--------------------------------------------------\n')

    # Create a look up table for distortion correction
    lutmapx, lutmapy = getDistortLUT()

    # Write OpenCV frames to Gstreamer stream (pipeout)
    gst_out = gstreamer_out(host=HOST, port=PORT)
    out = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(fps), (int(w), int(h)))

    if not out.isOpened():
        print('\n--------------------------------------------------\n' \
              'Failed to open output' \
              '\n--------------------------------------------------\n')
        exit()

    if cap.isOpened():
        # Give the camera time to warm up
        time.sleep(2.0)
        while True:
            try:
                ret_val, img = cap.read()

                if not ret_val:
                    break
                
                # Undistort the image
                undist_img = undistort_img(img, lutmapx, lutmapy)

                # Detect aruco tags
                arucoimg, corners, ids, rejectedImgPoints = detect_aruco_markup(undist_img)
                    
                if verbose:
                    print(f'[INFO] Corners: {corners}\n' \
                          f'[INFO] IDs: {ids}\n' \
                          f'[INFO] Rejected image points: {rejectedImgPoints}')

                out.write(arucoimg)
                cv2.waitKey(1)
            except KeyboardInterrupt:
                break
    else:
        print("pipeline open failed")

    print("successfully exit")


if __name__ == '__main__':
    args_parse()
    read_cam()