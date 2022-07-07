import numpy as np
import tkinter as tk
import socket
import threading
import argparse
from PIL import Image, ImageTk

#########################################################################
#                                                                       #
#   This program should be run on the client computer not the server!   #
#                                                                       #
#########################################################################

global HOST, PORT, screenW, screenW_2, screenH, screenH_2, tag_path, thread_running, displays

verbose = True

def args_parse():
    global HOST, PORT, screenW, screenW_2, screenH, screenH_2, tag_path, displays
    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', type=str, default="0.0.0.0", help="Host's port\n    (Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', type=int, default=5004, help="Host's port\n    (Default: 5004)")
    parser.add_argument('-w', '--screenW', type=int, default=1920, help="Screen width\n    (Default: 1920)")
    parser.add_argument('-ht', '--screenH', type=int, default=1080, help="Screen height\n    (Default: 1080)")
    parser.add_argument('-w2', '--screenW2', type=int, help="Second screen width\n    (Default: 1920)")
    parser.add_argument('-ht2', '--screenH2', type=int, help="Second screen height\n    (Default: 1080)")
    parser.add_argument('-t', '--tag', type=str, default="Tags/DICT_5X5_100_id1.png",
                        help="Filepath of the tag to display\n    (Default: Tags/DICT_5X5_100_id1.png)")
    parser.add_argument('-d', '--displays', type=int, default=2, help="Number of displays\n    (Default: 2)")
    args = parser.parse_args()
    HOST = args.host
    PORT = args.port
    screenW, screenW_2 = args.screenW, 1920 # args.screenW2
    screenH, screenH_2 = args.screenH, 1080 # args.screenH2
    tag_path = args.tag
    displays = args.displays

    if displays == 2 and ((screenW_2 is None) or (screenH_2 is None)):
        print(f"[ERROR] Specified 2 displays but did not specify the following:")
        if screenW_2 is None:
            print(f"    - Second screen width (-w2, --screenW2)")
        if screenH_2 is None:
            print(f"    - Second screen height (-ht2, --screenH2)")
        exit()

    if verbose:
        print(f"[INFO] Host: {HOST}\n"
              f"[INFO] Port: {PORT}\n"
              f"[INFO] Screen width: {screenW}\n"
              f"[INFO] Screen height: {screenH}\n"
              f"[INFO] Screen width 2: {screenW_2}\n"
              f"[INFO] Screen height 2: {screenH_2}\n"
              f"[INFO] Tag path: {tag_path}\n"
              f"[INFO] Displays: {displays}")


def recvcoord():
    global thread_running
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while thread_running:
            s.sendall(b"Data received from client!")
            data = s.recv(1024)
            data = data.decode('utf-8')
            data = eval(data)

class Background(object):
    def __init__(self, master, inputScreenW, inputScreenH):
        # Create a canvas on a tkinter frame
        self.frame = tk.Frame(master)
        self.frame.pack()
        self.can = tk.Canvas(self.frame,
                             bd=0,
                             highlightthickness=0,
                             bg="black",
                             width=inputScreenW,
                             height=inputScreenH)
        self.can.pack()
        master.update()

        # Get the width and height of the canvas
        self.canvasW, self.canvasH = self.can.winfo_width(), self.can.winfo_height()
        if verbose:
            print(f"[INFO] Canvas width: {self.canvasW}\n"
                  f"[INFO] Canvas height: {self.canvasH}")

        # Load the image and get the width and height of the image
        self.canImg = ImageTk.PhotoImage(Image.open(tag_path))
        self.imgW, self.imgH = self.canImg.width(), self.canImg.height()
        if verbose:
            print(f"[INFO] Image width: {self.imgW}\n"
                  f"[INFO] Image height: {self.imgH}")

        # Prevent the image from being garbage collected
        master.canImg = self.canImg

        # Find center of screen then get the x and y coordinates of where the upper left corner of the image will be
        # placed
        self.canCenterX, self.canCenterY = self.canvasW/2, self.canvasH/2
        if verbose:
            print(f"[INFO] Center X: {self.canCenterX}\n"
                  f"[INFO] Center Y: {self.canCenterY}")
        self.imgUpLeftX, self.imgUpLeftY = self.canCenterX - (self.imgW / 2), self.canCenterY - (self.imgH / 2)

        # Add a white, 50 pixel border around the image so it can be seen by the camera better and place the image onto
        # the canvas
        self.borderRect = self.can.create_rectangle(self.imgUpLeftX - 50,
                                                    self.imgUpLeftY - 50,
                                                    self.imgUpLeftX + self.imgW + 50,
                                                    self.imgUpLeftY + self.imgH + 50,
                                                    fill="white")
        self.can.create_image(self.imgUpLeftX, self.imgUpLeftY, anchor=tk.NW, image=self.canImg)
        # TODO: Add socket connection compatibility so that the image can be moved around the screen after the tag is
        #       detected. ie, detect -> readjust position


def start(inputScreenW=None, inputScreenH=None):
    if inputScreenW is None:
        inputScreenW = screenW
    if inputScreenH is None:
        inputScreenH = screenH
    # Create a window and start it in fullscreen mode
    root = tk.Tk()

    # Account for if there are 2 displays
    if displays == 2:
        root.geometry(f"{screenW_2}x{screenH_2}+{inputScreenW}+0")
    else:
        root.geometry(f"{inputScreenW}x{inputScreenH}")

    root.overrideredirect(1)

    # Create a background object
    Background(root, inputScreenW, inputScreenH)
    root.mainloop()


if __name__ == "__main__":
    args_parse()
    start()