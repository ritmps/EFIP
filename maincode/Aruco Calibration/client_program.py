import numpy as np
import tkinter as tk
from tkinter import *
import socket
import threading
import argparse

#########################################################################
#                                                                       #
#   This program should be run on the client computer not the server!   #
#                                                                       #
#########################################################################

global HOST, PORT

verbose = True

def args_parse():
    global HOST, PORT, screenW, screenH
    parser = argparse.ArgumentParser(description='Run GStreamer RTP stream')
    parser.add_argument('-i', '--host', type=str, default="0.0.0.0", help="Host's port\n    (Default: 0.0.0.0)")
    parser.add_argument('-p', '--port', type=int, default=5004, help="Host's port\n    (Default: 5004)")
    parser.add_argument('-w', '--screenW', type=int, default=1920, help="Screen width\n    (Default: 1920)")
    parser.add_argument('-ht', '--screenH', type=int, default=1080, help="Screen height\n    (Default: 1080)")
    args = parser.parse_args()
    HOST = args.host
    PORT = args.port
    screenW = args.screenW
    screenH = args.screenH
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
        self.frame = tk.Frame(master)
        self.frame.pack()
        self.can = tk.Canvas(self.frame)
        self.can.pack()

def start(screenW, screenH):
        root = tk.Tk()
        root.geometry(f"{screenW}x{screenH}")
        root.wm_attributes('-fullscreen', 'True')
        root.mainloop()

if __name__ == "__main__":
    args_parse()
    start(screenW, screenH)