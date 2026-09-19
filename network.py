import socket
import pickle
import struct
from shared import *

class Network:
    def __init__(self) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server = "0.0.0.0"
        self.port = 1234
        self.address = (self.server, self.port)
        self.client.settimeout(2.0)
        self.connected = False
        self.id = -1

    def disconnect(self):
        if not self.connected: return
        self.send(Action.EXITED)

    def set_address(self, ip, port):
        self.server = ip
        self.port = port
        self.address = (ip, port)

    def connect(self):
        try:
            print(f"Attempting connection to {self.address}")
            self.client.connect(self.address)
            # returned = pickle.loads(self.client.recv(4096))
            self.send(Action.JOINED)
            returned = self.recv_data()
            self.id = returned["client_id"]
            # returned = self.recv_data()
            if returned == None: return None
            self.connected = True
            return returned
        except:
            pass

    def send(self, action:Action, data:list=[]):
        message = {"client_id": self.id, "action": action}
        if action != Action.UPDATE:
            print(f"sending {action.name}")
        match action:
            case Action.JOINED:
                pass
            case Action.PLACE:
                if len(data) < 2: return
                message["x"] = data[0]
                message["y"] = data[1]
            case Action.REMOVE:
                if len(data) < 2: return
                message["x"] = data[0]
                message["y"] = data[1]
            case Action.ATTACK:
                if len(data) < 2: return
                message["x"] = data[0]
                message["y"] = data[1]
            case Action.EXITED:
                pass
            case Action.RESET:
                message["reset"] = True

        self.send_data(message)
        # returned = self.recv_data()
        # return returned

    # def send(self, data):
    #     try:
    #         self.send_data(data)
    #         return self.recv_data()
            # self.client.send(pickle.dumps(data))
            # raw = self.client.recv(4096)
            #

            # if not raw:
            #     print("Disconected from server")
            #     self.disconnect()
            # else:
            #     return pickle.loads(raw)
        # except socket.error as e:
        #     print(e)

    def send_data(self, data):
        payload = pickle.dumps(data)

        header = struct.pack("!I", len(payload))
        self.client.sendall(header)
        self.client.sendall(payload)


    def recv_exact(self, size):
        data = b""

        while len(data) < size:
            chunk = self.client.recv(size - len(data))

            if not chunk:
                raise ConnectionError("Connection closed")

            data += chunk

        return data


    def recv_data(self):  # AI FIX FOR TRUNICATED PICKLE FILES # TODO maybe fix later myself
        # Read message length
        header = self.recv_exact(4)
        size = struct.unpack("!I", header)[0]

        # Read complete pickle
        payload = self.recv_exact(size)

        # IMPORTANT: convert bytes -> Python object
        obj = pickle.loads(payload)
        return obj
