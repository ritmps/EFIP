import numpy as np
import tkinter as tk
import socket
import threading
import argparse
import PIL as pil

#########################################################################
#                                                                       #
#   This program should be run on the client computer not the server!   #
#                                                                       #
#########################################################################

global HOST, PORT, screenW, screenH, tag_path

verbose = True

def args_parse():
    global HOST, PORT, screenW, screenH, tag_path
    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', type=str, default="0.0.0.0", help="Host's port\n    (Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', type=int, default=5004, help="Host's port\n    (Default: 5004)")
    parser.add_argument('-w', '--screenW', type=int, default=1920, help="Screen width\n    (Default: 1920)")
    parser.add_argument('-ht', '--screenH', type=int, default=1080, help="Screen height\n    (Default: 1080)")
    parser.add_argument('-t', '--tag', type=str, default="Tags/DICT_5X5_100_id1.png", help="Filepath of the tag to display\n    (Default: Tags/DICT_5X5_100_id1.png)")
    args = parser.parse_args()
    HOST = args.host
    PORT = args.port
    screenW = args.screenW
    screenH = args.screenH
    tag_path = args.tag
    print(f'Host: {HOST}\nPort: {PORT}')

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

class Background(object):
    def __init__(self, master, screenW, screenH):
        # Create a canvas on a tkinter frame
        self.frame = tk.Frame(master)
        self.frame.pack()
        self.can = tk.Canvas(self.frame)
        self.can.pack()

        # Get the width and height of the canvas
        self.canvasW, self.canvasH = self.can.winfo_width(), self.can.winfo_height()

        # Load the image
        self.canImg = pil.ImageTK.PhotoImage(pil.Image(file=tag_path))

        # Get the width and height of the image
        self.imgW, self.imgH = self.canImg.width(), self.canImg.height()

def start(screenW, screenH):
    # Create a window and start it in fullscreen mode
    root = tk.Tk()
    root.geometry(f"{screenW}x{screenH}")
    root.wm_attributes('-fullscreen', 'True')
    root.mainloop()

if __name__ == "__main__":
    args_parse()
    start(screenW, screenH)