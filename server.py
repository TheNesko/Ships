import socket
from _thread import *

from player import Player
import pickle
import time

class GameServer:
    def __init__(self, server_ip = "10.59.61.151", server_port = 5555) -> None:
        self.hostname = socket.gethostname()
        self.server_ip = server_ip
        self.server_port = server_port
        self.shutdown_request = False
        self.started = False

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.settimeout(2.0)

        self.pool = []
        self.names = {}
        self.players = [Player(), Player()]
        self.turn = 0
        self.reseting = False

    def host(self, address, port):
        try:
            self.server_socket.bind((address,port))
        except socket.error as e:
            print(e)
            return False
        self.server_socket.listen(2)

        print(f"{self.hostname} started server at {address}:{port}")
        return True

    def connect_client(self, client):
        self.pool.append(client)
        self.names[client] = f"Player{len(self.pool)}"
        print(f"{self.names[client]} connected")

    def disconect_client(self, client, player):
        self.pool.remove(client)
        client_name = self.names.pop(client)
        print(f"{client_name} disconnected")
        client.close()
        self.players[player] = Player()

    def stop_server(self):
        self.shutdown_request = True
        self.started = False


    def client_thred(self, client, address, player):
        self.connect_client(client)
        print(f"{address} joined the game")
        client.send(pickle.dumps(self.players[player]))
        reply = ""
        while not self.shutdown_request:
            try:
                raw = client.recv(2048)

                if not raw:
                    print(f"{self.names[client]} disconnected")
                    break

                data = pickle.loads(raw)

                if self.players[0].request_reset and self.players[1].request_reset:
                    self.reseting = True
                if self.reseting:
                    if not self.players[0].request_reset and not self.players[1].request_reset:
                        self.reseting = False
                    else:
                        reply = {
                        "p1" : Player(),
                        "p2" : Player()}
                        client.sendall(pickle.dumps(reply))
                        continue
                else:
                    self.players[player] = data

                if self.players[player].finished_turn:
                    self.turn += 1
                    self.players[player].my_turn = False
                    self.players[player].finished_turn = False

                self.players[self.turn%2].my_turn = True

                if player == 1:
                    reply = {
                    "p1" : self.players[1],
                    "p2" : self.players[0]}
                else:
                    reply = {
                    "p1" : self.players[0],
                    "p2" : self.players[1]}

                    # print(f"Received: {data}")
                    # print(f"Sending: {reply}")

                client.sendall(pickle.dumps(reply))
            except TimeoutError:
                continue
            except Exception as e:
                print(e)
                break
        self.disconect_client(client, player)

    def start_server(self, address="", port=-1):
        self.started = False
        address = self.server_ip if address == "" else address
        port = self.server_port if port == -1 else port
        self.server_ip = address
        self.server_port = port
        print(f"Starting server at {address}:{port}")
        if self.host(address, port) == False:
            print("Server failed to start")
            return
        self.started = True
        self.shutdown_request = False
        current_player = 0
        while not self.shutdown_request:
            try:
                client, address = self.server_socket.accept()
                print(f"connected to {address}")

                start_new_thread(self.client_thred, (client, address, current_player))
                current_player += 1
                if current_player >= 2:
                    break
            except TimeoutError:
                continue

        time.sleep(0.1)
        print("---------------------")
        print("All players connected")
        print("---------------------")
        while self.pool:
            time.sleep(0.1)
        self.server_socket.close()
        print("Server closed")
        self.shutdown_request = False
        self.started = False

if __name__ == "__main__":
    server = GameServer()
    server.start_server()
