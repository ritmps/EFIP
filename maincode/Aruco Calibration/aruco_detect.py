import argparse
import math
import time
import imutils
import cv2
from cv2 import aruco
import numpy as np
import sys
import multiprocessing as mp

global HOST, PORT, lutPath, directory, arucoDict

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

# Timer class to calculate the average time of a function
class timer:
    global verbose, timings
    
    # Initialize the timer setting the average time, number of times it was called, the start time,
    # and the current duration of the timer all to 0.
    def __init__(self):
        self.avg = 0
        self.count = 0
        self.start = 0
        self.curDuration = 0
    
    # Set the start time of the timer, ie. start the timer.
    def start_timer(self, action: str = None):
        self.start = time.time()
        if action is ((not None) and (verbose)):
                print(f'[INFO] {action.upper()} STARTED')

    # If verbose is active, print the duration of the timer.
    # If timings is active, update the average time of the timer.
    def update(self, action: str):
        if verbose or timings:
            self.curDuration = (time.time() - self.start) * 1000
            if verbose:
                print(f'[INFO] {action.upper()} TOOK {self.curDuration}ms')
            if timings:
                self.update_average()

    # Update the average time of the timer with a moving average 
    # ("new average" = ("current calculated time of the timer" - "old average") / "number of times the timer was called")
    def update_average(self):
        self.count += 1
        self.avg = self.avg + ((self.curDuration - self.avg) / self.count)
        self.start_timer()

    # Return the average time of the timer.
    def get_average(self):
        return self.avg
    
    # Return the duration of the timer.
    def get_curDuration(self):
        return self.curDuration

# Timer for how long it takes the lookup table to be loaded
lutTime = timer()
# Timer for how long it takes the remap table to be loaded
remapTime = timer()
# Timer for how long it takes to undistort the stream
avgUndistTime = timer()
# Timer for how long it takes to detect the aruco markers
avgDetectTime = timer()

# Parse the command line arguments
def args_parse():
    global HOST, PORT, lutPath, remapPath, directory, arucoDict
    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', type=str, default="0.0.0.0", help="Host's port\n    (Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', type=int, default=5004, help="Host's port\n    (Default: 5004)")
    parser.add_argument('-l', '--lookup', type=str, default="../lookup_table.csv", help="Path to lookup table\n    (Default: /workspaces/EFIP/maincode/lookup_table.csv)")
    parser.add_argument('-r', '--remap', type=str, default="../remap.csv", help="Path to remap table\n    (Default: /workspaces/EFIP/maincode/remap.csv)")
    parser.add_argument('-d', '--directory', type=str, default="Tags", help="Directory to ArUCo tags\n    (Default: Tags)")
    parser.add_argument('-t', '--type', type=str, default="DICT_4X4_50", help="Type of ArUCo tag to detect\n    (Default: DICT_5X5_100)")
    args = parser.parse_args()
    if ARUCO_DICT[args.type] == None:
        print(f'[INFO] ARUCO TAG TYPE: {args.type} IS NOT SUPPORTED')
        sys.exit(0)
    HOST = args.host
    PORT = args.port
    lutPath = args.lookup
    remapPath = args.remap
    directory = args.directory
    arucoDict = cv2.aruco.Dictionary_get(ARUCO_DICT[args.type])
    if verbose:
        print(f'[INFO] Host: {HOST}\n' \
              f'[INFO] Port: {PORT}\n' \
              f'[INFO] Lookup table: {lutPath}\n' \
              f'[INFO] Directory: {directory}\n' \
              f'[INFO] Tag type: {arucoDict}')
    print(f'Host: {HOST}\nPort: {PORT}')

# Define the gstreamer input pipeline
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

# Define the gstreamer output pipeline
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

# Load the Lookup Table from the csv file labeled lookup_table.csv
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

# Load the remap Table from the csv file labeled remap.csv
def getRemapLUT():
    global remapTime
    remapTime.start_timer()
    
    print(f"[INFO] LOADING REMAP TABLE: {remapPath}\n" \
        f"[INFO] PLEASE BE PATIENT, THIS CAN TAKE A MOMENT...")

    # Read the csv file and store in 2D array
    remap_lut = np.loadtxt(remapPath, delimiter=',', dtype=np.float32)
    
    # Split the array into mapx and mapy
    mapx, mapy = np.vsplit(remap_lut, 2)

    remapTime.update('loading remap table')
    return (mapx, mapy)

# Function to undistort the image using the look up table
def undistort_img(image, lutmapx, lutmapy):
    global avgUndistTime
    avgUndistTime.start_timer('undistorting image')
    
    # Undistort the image using the look up table
    undist = cv2.remap(image, lutmapx, lutmapy, cv2.INTER_LINEAR)

    avgUndistTime.update('undistorting image')
    return undist

# Function to detect the aruco marker corners, ids, and rejected image points without marking up the image
def detect_aruco(image):
    global avgDetectTime
    avgDetectTime.start_timer('detecting aruco tags')
	
    # detect aruco tags
    parameters = cv2.aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, arucoDict, parameters=parameters)

    if len(corners) > 0:
        ids = ids.flatten()
        for (markerCorner, markerID) in zip(corners, ids):
            # Extract the marker corners (returned in order: top left, top right, bottom right, bottom left)
            cornersTemp = markerCorner.reshape((4, 2))
            (topLeft, topRight, bottomRight, bottomLeft) = cornersTemp

            topRight = (int(topRight[0]), int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
            topLeft = (int(topLeft[0]), int(topLeft[1]))
    
    avgDetectTime.update('detecting aruco tags')
    return corners, ids

# Returns corners, ids, rejected image points, and marks up an image using the detected points
def detect_aruco_markup(image):
    global avgDetectTime
    avgDetectTime.start_timer('detecting aruco tags')
    
    # detect aruco tags
    parameters = cv2.aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, arucoDict, parameters=parameters)
    # draw aruco tags
    if len(corners) > 0:
        ids = ids.flatten()
        for (markerCorner, markerID) in zip(corners, ids):
            # Extract the marker corners (returned in order: top left, top right, bottom right, bottom left)
            singleCorners = markerCorner.reshape((4, 2))
            (topLeft, topRight, bottomRight, bottomLeft) = singleCorners

            topRight = (int(topRight[0]), int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
            topLeft = (int(topLeft[0]), int(topLeft[1]))

            # Draw bounding box of ArUCo detection and the center coordinates
            cv2.line(image, topLeft, topRight, (0, 255, 0), 2)
            cv2.line(image, topRight, bottomRight, (0, 255, 0), 2)
            cv2.line(image, bottomRight, bottomLeft, (0, 255, 0), 2)
            cv2.line(image, bottomLeft, topLeft, (0, 255, 0), 2)

            cX = int((topLeft[0] + bottomRight[0]) / 2.0)
            cY = int((topLeft[1] + bottomRight[1]) / 2.0)
            cv2.circle(image, (cX, cY), 4, (0, 0, 255), -1)

            # Draw the ID of the marker
            cv2.putText(image, str(markerID), (topLeft[0], topLeft[1] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    avgDetectTime.update('detecting aruco tags')
    return image, corners, ids

# dimensions of the table:
# length = ~ 74.375 inches
# width = ~ 36.6875 inches
# distance between circles and top / bottom of table = ~ 6.6875 inches
# distance between circles and left / right of table = ~ 12.1875 inches
# distance between circles lengthwise = ~ 46 inches
# distance between circles widthwise = ~ 23.3125 inches
class homographyGenerator:
    def __init__(self, maxiter=100):
        self.length = 74.375
        self.width = 36.6875
        self.circle_distance_top_bottom = 6.6875
        self.circle_distance_left_right = 12.1875
        self.circle_distance_lengthwise = 46
        self.circle_distance_widthwise = 23.3125
        self.avgCorners = None
        self.centers = None
        self.idealcenters = None
        self.iterations = 1

        # Dictionary to help keep track of indices in arrays
        self.dict = {
            'TL': 0,
            'TR': 1,
            'BR': 2,
            'BL': 3,
            'x': 0,
            'y': 1
        } 
    
    # KEEP IN MIND THIS PROGRAM ONLY ACCEPTS ARUCO TAGS WITH IDS 1-5
    def updateCorners(self, corners, ids):
        # Check if any markers were detected
        if len(ids) > 0:
            # Check if the average corners array has been initialized
            if self.avgCorners is None:
                for (markerCorner, markerID) in zip(corners, ids):
                    if verbose:
                        print(f'[INFO] Marker ID: {markerID}')
                    # Extract each of the detected marker's corners (returned in order: top left, top right, bottom right, bottom left)
                    singleCorners = markerCorner.reshape((4, 2))
                    (topLeft, topRight, bottomRight, bottomLeft) = singleCorners

                    topLeft = (int(topLeft[0]), int(topLeft[1]))
                    topRight = (int(topRight[0]), int(topRight[1]))
                    bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                    bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))

                    # If the row is 0, then 
                    if row == 0:
                        self.avgCorners = np.array([[topLeft, topRight, bottomRight, bottomLeft]])
                        if verbose:
                            print(f'[INFO] Average Corners: {self.avgCorners}')
                    else:
                        self.avgCorners = np.vstack((self.avgCorners, [[topLeft, topRight, bottomRight, bottomLeft]]))
                    self.dict[markerID] = row
                    row += 1
            # If average corners is defined, then update it.
            else:
                for (markerCorner, markerID) in zip(corners, ids):
                    # If the marker is in the dictionary already, update the average corners
                    if markerID in self.dict:
                        row = self.dict[markerID]
                        singleCorners = markerCorner.reshape((4, 2))
                        (topLeft, topRight, bottomRight, bottomLeft) = singleCorners

                        topLeft = (int(topLeft[0]), int(topLeft[1]))
                        topRight = (int(topRight[0]), int(topRight[1]))
                        bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                        bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))

                        self.avgCorners[row][self.dict['TL']] = (
                            (self.avgCorners[row][0][0] + ((topLeft[0] - self.avgCorners[row][0][0]) / self.iterations)),
                            (self.avgCorners[row][0][1] + ((topLeft[1] - self.avgCorners[row][0][1]) / self.iterations))
                        )
                        self.avgCorners[row][self.dict['TR']] = (
                            (self.avgCorners[row][1][0] + ((topRight[0] - self.avgCorners[row][1][0]) / self.iterations)),
                            (self.avgCorners[row][1][1] + ((topRight[1] - self.avgCorners[row][1][1]) / self.iterations))
                        )
                        self.avgCorners[row][self.dict['BR']] = (
                            (self.avgCorners[row][2][0] + ((bottomRight[0] - self.avgCorners[row][2][0]) / self.iterations)),
                            (self.avgCorners[row][2][1] + ((bottomRight[1] - self.avgCorners[row][2][1]) / self.iterations))
                        )
                        self.avgCorners[row][self.dict['BL']] = (
                            (self.avgCorners[row][3][0] + ((bottomLeft[0] - self.avgCorners[row][3][0]) / self.iterations)),
                            (self.avgCorners[row][3][1] + ((bottomLeft[1] - self.avgCorners[row][3][1]) / self.iterations))
                        )
                    # If the marker is not in the dictionary, add it to the dictionary and the average corners array
                    else:
                        row = self.avgCorners.shape[0] - 1
                        singleCorners = markerCorner.reshape((4, 2))
                        (topLeft, topRight, bottomRight, bottomLeft) = singleCorners

                        topLeft = (int(topLeft[0]), int(topLeft[1]))
                        topRight = (int(topRight[0]), int(topRight[1]))
                        bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                        bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))

                        self.avgCorners = np.vstack((self.avgCorners, [[topLeft, topRight, bottomRight, bottomLeft]]))
                        self.dict({markerID:row})

        # Increment the iteration number
        self.iterations += 1        

    # def updateCenters(self, corners):
    #     for row in range(self.avgCorners.shape[0]):
    #         # Extract the marker corners (returned in order: top left, top right, bottom right, bottom left)
    #         singleCorners = markerCorner.reshape((4, 2))
    #         (topLeft, topRight, bottomRight, bottomLeft) = singleCorners

    #         topRight = (int(topRight[0]), int(topRight[1]))
    #         bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))

    #         # Calculate the center of the marker
    #         cX = (topLeft[0] + bottomRight[0]) / 2.0
    #         cY = (topLeft[1] + bottomRight[1]) / 2.0

    #         # If there is nothing in the list, add the center of the marker to the list
    #         # Final value in the list is the iteration number for the given marker
    #         if self.avgCenters == None:
    #             self.avgCenters = np.array([[markerID, cX, cY, 1]])
            
    #         # If the markerID is already in the list, average the center of the marker with the existing center
    #         elif (markerID in self.avgCenters[:, 0]):
    #             row = np.where(self.avgCenters[:, 0] == markerID)
    #             self.avgCenters[row, 1] = self.avgCenters[row, 1] + ((cX - self.avgCenters[row, 1]) / self.avgCenters[row, 3])
    #             self.avgCenters[row, 2] = self.avgCenters[row, 2] + ((cY - self.avgCenters[row, 2]) / self.avgCenters[row, 3])
    #             self.avgCenters[row, 3] = self.avgCenters[row, 3] + 1
            
    #         # If the markerID is not in the list, add the center of the marker to the list
    #         else:
    #             avgCenters = np.vstack((avgCenters, [markerID, cX, cY, 1]))

    # def genHomographyInit(self, corners, ids, img=None):
        # Find centers for id 1, 2, 3, and 4 and get their coordinates
        

    #     if (1 in avgCenters[:, 0]):
    #         row = np.where(avgCenters[:, 0] == 1)
    #         c1 = (avgCenters[row, 1], avgCenters[row, 2])
    #     else:
    #         exit('[ERROR] ID 1 NOT FOUND IN AVERAGE CENTERS')
    #     if (2 in avgCenters[:, 0]):
    #         row = np.where(avgCenters[:, 0] == 2)
    #         c2 = (avgCenters[row, 1], avgCenters[row, 2])
    #     else:
    #         exit('[ERROR] ID 2 NOT FOUND IN AVERAGE CENTERS')
    #     if (3 in avgCenters[:, 0]):
    #         row = np.where(avgCenters[:, 0] == 3)
    #         c3 = (avgCenters[row, 1], avgCenters[row, 2])
    #     else:
    #         exit('[ERROR] ID 2 NOT FOUND IN AVERAGE CENTERS')
    #     if (4 in avgCenters[:, 0]):
    #         row = np.where(avgCenters[:, 0] == 4)
    #         c4 = (avgCenters[row, 1], avgCenters[row, 2])
    #     else:
    #         exit('[ERROR] ID 2 NOT FOUND IN AVERAGE CENTERS')
        
    #     # Find distance between c1 and c2
    #     if (((c1[0] - c2[0]) ** 2) + ((c1[1] - c2[1]) ** 2)) < 0:
    #         dstBtwCtrs_1_2 = math.sqrt(((c2[0] - c1[0]) ** 2) + ((c2[1] - c1[1]) ** 2))
    #     else:
    #         dstBtwCtrs_1_2 = -math.sqrt(((c1[0] - c2[0]) ** 2) + ((c1[1] - c2[1]) ** 2))
        
    #     # Find distance between c1 and c3
    #     if (((c1[0] - c3[0]) ** 2) + ((c1[1] - c3[1]) ** 2)) < 0:
    #         dstBtwCtrs_1_3 = math.sqrt(((c3[0] - c1[0]) ** 2) + ((c3[1] - c1[1]) ** 2))
    #     else:
    #         dstBtwCtrs_1_3 = -math.sqrt(((c1[0] - c3[0]) ** 2) + ((c1[1] - c3[1]) ** 2))

    #     # Find which coordinate has the largest y value (bottom of image) and calculate the ideal image
    #     # point which is dstBtwCtrs_1_2 away from the coordinate with the lowest y value (correct rotation)
    #     if c1[1] > c2[1]:
    #         idealc1 = (c1[0], c1[1])
    #         idealc2 = (c1[0] + dstBtwCtrs_1_2, c1[1])
    #         idealc3 = (c1[0], c1[1] + dstBtwCtrs_1_3)
    #         idealc4 = (c1[0] + dstBtwCtrs_1_2, c1[1] + dstBtwCtrs_1_3)
    #     else:
    #         idealc1 = (c2[0] + dstBtwCtrs_1_2, c2[1])
    #         idealc2 = (c2[0], c2[1])
    #         idealc3 = (c2[0] + dstBtwCtrs_1_2, c2[1] - dstBtwCtrs_1_3)
    #         idealc4 = (c2[0], c2[1] - dstBtwCtrs_1_3)

    #     # Create 2 lists of points to be used in the homography
    #     ptsInit = np.array([[[c1[0], c1[1]]], 
    #                         [[c2[0], c2[1]]],
    #                         [[c3[0], c3[1]]],
    #                         [[c4[0], c4[1]]]], np.float32)
    #     ptsInit = ptsInit.reshape((4, 1, 2))
    #     print(f'[INFO] SHAPE: {ptsInit.shape}')
    #     print(f'[INFO] PTS: {ptsInit}')
    #     ptsProj = np.array([[[idealc1[0], idealc1[1]]], 
    #                         [[idealc2[0], idealc2[1]]],
    #                         [[idealc3[0], idealc3[1]]],
    #                         [[idealc4[0], idealc4[1]]]], np.float32)
    #     ptsProj = ptsProj.reshape((4, 1, 2))
    #     print(f'[INFO] SHAPE: {ptsProj.shape}')
    #     print(f'[INFO] PTS: {ptsProj}')

    #     # Calculate the homography
    #     h, status = cv2.findHomography(ptsInit, ptsProj)

    #     # Apply the homography to the image
    #     img_warped = cv2.warpPerspective(img, h, (1920, 1080))
    #     return img_warped

homographyGen = homographyGenerator()

def read_cam():
    global img, stop_thread, verbose

    # First iteration of the while loop = true
    firstloop = True

    # Stop any running threads = false
    stop_thread = False

    # Create a look up table for distortion correction
    lutmapx, lutmapy = getRemapLUT()

    if verbose:
        print(f"[INFO] READING CAMERA PIPELINE...")
    # Read Gstreamer pipeline into OpenCV (pipein)
    cap = cv2.VideoCapture(gstreamer_in(), cv2.CAP_GSTREAMER)
    if verbose:
        print(f"[INFO] SUCCESSFULLY READ CAMERA PIPELINE")

    # Get the width, height and fps of the stream and print it to the console
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f'\n--------------------------------------------------\n' \
          f'Src opened, {w}x{h} @ {fps} fps' \
          f'\n--------------------------------------------------\n')

    # Write OpenCV frames to Gstreamer stream (pipeout)
    gst_out = gstreamer_out(host=HOST, port=PORT)
    out = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(fps), (int(w), int(h)))

    if not out.isOpened():
        print('\n--------------------------------------------------\n' \
              'Failed to open output' \
              '\n--------------------------------------------------\n')
        exit()

    iter = 0

    if verbose:
        loop_verbose = True
    elif not verbose:
        loop_verbose = False

    if cap.isOpened():
        # Give the camera time to warm up
        time.sleep(2.0)
        while True:
            try:
                iter = iter + 1
                if loop_verbose:
                    if iter % 50 == 0:
                        verbose = True
                    else:
                        verbose = False

                ret_val, img = cap.read()

                if not ret_val:
                    break
                
                if iter < 100:
                    # Undistort the image
                    undist_img = undistort_img(img, lutmapx, lutmapy)

                    # Detect aruco tags
                    arucoImg, corners, ids = detect_aruco_markup(undist_img)
                    
                    homographyGen.updateCorners(corners, ids)

                    out.write(arucoImg)
                    cv2.waitKey(1)
                else:
                    # Undistort the image
                    undist_img = undistort_img(img, lutmapx, lutmapy)

                    # Detect aruco tags
                    arucoImg, corners, ids = detect_aruco_markup(undist_img)

                    # Write the image to the Gstreamer stream
                    out.write(arucoImg)
                    cv2.waitKey(1)
            except KeyboardInterrupt:
                break
    else:
        print("pipeline open failed")

    print("successfully exit")


if __name__ == '__main__':
    args_parse()
    read_cam()