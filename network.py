import socket
import pickle

class Network:
    def __init__(self) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server = "10.59.61.151"
        self.port = 5555
        self.address = (self.server, self.port)
        self.client.settimeout(2.0)
        self.connected = False

    def disconnect(self):
        if not self.connected: return
        self.client.close()
        self.__init__()

    def set_address(self, ip, port):
        self.server = ip
        self.port = port
        self.address = (ip, port)

    def connect(self):
        try:
            print(f"Attempting connection to {self.address}")
            self.client.connect(self.address)
            returned = pickle.loads(self.client.recv(4096))
            if returned == None: return None
            # self.client.settimeout(None)
            self.connected = True
            return returned
        except:
            pass

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            raw = self.client.recv(4096)

            if not raw:
                print("Disconected from server")
                self.disconnect()
            else:
                return pickle.loads(raw)
        except socket.error as e:
            print(e)
