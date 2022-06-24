import socket
import sys

HOST = "129.21.58.246"  # The server's hostname or IP address
PORT = 9998  # The port used by the server


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        try:
            s.sendall(b"Data received from client!")
            data = s.recv(1024)

            print(f"Received {data!r}")
        except KeyboardInterrupt:
            break

# import socket
# import sys

# HOST, PORT = "129.21.58.246", 9998
# data = " ".join(sys.argv[1:])

# # Create a socket (SOCK_STREAM means a TCP socket)
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#     # Connect to server and send data
#     sock.connect((HOST, PORT))
#     sock.sendall(bytes(data + "\n", "utf-8"))

#     # Receive data from the server and shut down
#     received = str(sock.recv(1024), "utf-8")

# print("Sent:     {}".format(data))
# print("Received: {}".format(received))
