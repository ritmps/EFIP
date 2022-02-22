import socket
import threading

# header tells us how big the message will be in bytes
HEADER = 64
PORT = 8080
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        # decode from its bytes format to utf-8
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            #finds the length and sets that as the amount we will recieve
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False

        print(f"[{addr}] {msg}")
        conn.send("msg recieved".encode(FORMAT))

    conn.close()
        


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        # vv this line will wait for a new connection to the server
        # it will store the adress and create an object allowing us to communicate back
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        #since there will always be one thread running(this thread) we subtract 1
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

print("[STARTING] server is starting...")
start()