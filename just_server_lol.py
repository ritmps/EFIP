# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostName = "localhost"
serverPort = 8080

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

# # MIT License
# # Copyright (c) 2019-2022 JetsonHacks

# # Using a CSI camera (such as the Raspberry Pi Version 2) connected to a
# # NVIDIA Jetson Nano Developer Kit using OpenCV
# # Drivers for the camera and OpenCV are included in the base image
# print('test')
# from http.server import BaseHTTPRequestHandler, HTTPServer
# import cv2
# import asyncio
# import websockets
# import time
# import json
# import random

# COORDINATES = ''

# async def socket_connected(websocket, path):
#     print(path)
# #     while True:
# #         try:
# #             await websocket.send(COORDINATES)
# #             await websocket.recv()
# #         except Exception:
# #             break

# # # async def show_camera():
# # #     while True:
# # #         print('sleeping...')
# # #         await asyncio.sleep(1)
# # #         COORDINATES = json.dumps([random.randint(1,100),random.randint(1,100)])
        
# # from flask import Flask, request
# # app = Flask(__name__)
# # @app.route('/', methods=['POST'])
# # def result():
# #     print(request.form['foo']) # should display 'bar'
# #     return 'Received !' # response to your request.

# def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
#     server_address = ('', 8000)
#     httpd = server_class(server_address, handler_class)
#     httpd.serve_forever()
# run()


# # # asyncio.get_event_loop().run_until_complete(show_camera())
# # print('should see this')
# # asyncio.get_event_loop().run_until_complete(websockets.serve(socket_connected, port = 5000))
# # print('should see this12')
# # asyncio.get_event_loop().run_forever()


# # print('should not see this')
