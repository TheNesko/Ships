from random import randint
import socket
from _thread import *

from player import Player
import pickle
import time
import struct

from shared import Action

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
        self.ready_players = 0
        self.match_started = False
        self.reset_requests = 0

    def host(self, address, port):
        try:
            self.server_socket.bind((address,port))
        except socket.error as e:
            print(f"host error: {e}")
            return False
        self.server_socket.listen(2)

        print(f"{self.hostname} started server at {address}:{port}")
        return True

    def connect_client(self, client):
        self.pool.append(client)
        self.names[client] = f"Player{len(self.pool)}"
        print(f"{self.names[client]} connected")

    def disconect_client(self, client, player):
        if client not in self.pool: return
        self.pool.remove(client)
        client_name = self.names.pop(client)
        print(f"{client_name} disconnected")
        client.close()
        self.players[player] = Player()

    def stop_server(self):
        self.shutdown_request = True
        self.started = False

    def send_data(self, client, data):
        payload = pickle.dumps(data)

        header = struct.pack("!I", len(payload))
        client.sendall(header)
        client.sendall(payload)

    def send_to_others(self, client, data):
        payload = pickle.dumps(data)

        header = struct.pack("!I", len(payload))
        for other in self.pool:
            if other == client: continue
            other.sendall(header)
            other.sendall(payload)

    def recv_exact(self, client, size):
        data = b""

        while len(data) < size:
            chunk = client.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")

            data += chunk

        return data


    def recv_data(self, client):
        # Read message length
        header = self.recv_exact(client, 4)
        size = struct.unpack("!I", header)[0]
        # Read complete pickle
        payload = self.recv_exact(client, size)
        # IMPORTANT: convert bytes -> Python object
        obj = pickle.loads(payload)

        return obj


    def client_thred(self, client, address, player_id):
        print(f"{address} joined the game")
        self.connect_client(client)
        # client.send(pickle.dumps(self.players[player]))
        # self.send_data(client, self.players[player])
        while not self.shutdown_request:
            try:
                # raw = client.recv(4096)

                # if not raw:
                #     print(f"{self.names[client]} disconnected")
                #     break

                # data = pickle.loads(raw)
                player = self.players[player_id]
                data = self.recv_data(client)

                if data == "":
                    break

                action = data["action"]

                reply = {"client_id": player_id, "action": action}
                match action:
                    case Action.JOINED:
                        reply["attack_board"] = self.players[0 if player_id == 1 else 1].ship_board
                        _reply = reply.copy()
                        _reply["attack_board"] = player.ship_board
                        self.send_to_others(client, _reply)
                    case Action.PLACE:
                        x = data["x"]
                        y = data["y"]
                        result = player.ship_board.place_ship(x, y)
                        reply["result"] = result
                        if result == None: continue
                        reply["x"] = x
                        reply["y"] = y
                        if result:
                            self.send_to_others(client, reply)
                    case Action.REMOVE:
                        x = data["x"]
                        y = data["y"]
                        result = player.ship_board.remove_ship(x, y)
                        reply["result"] = result
                        if result == None: continue
                        reply["x"] = x
                        reply["y"] = y
                        if result:
                            self.send_to_others(client, reply)
                    case Action.ATTACK:
                        x = data["x"]
                        y = data["y"]
                        result = self.players[0 if player == 1 else 1].ship_board.attack(x, y)
                        reply["result"] = result
                        if result == None: continue
                        reply["x"] = x
                        reply["y"] = y
                        reply["my_turn"] = player_id if result == True else (player_id+1)%2
                        self.send_to_others(client, reply)
                    case Action.READY:
                        player.ready = not player.ready if self.ready_players != 2 else True
                        self.ready_players = 1 if self.players[0].ready or self.players[1].ready else 0
                        self.ready_players = 2 if self.players[0].ready and self.players[1].ready else self.ready_players
                        if self.ready_players == 2:
                            self.match_started = True
                        reply["ready_player"] = self.ready_players
                        reply["match_started"] = self.match_started
                        reply["my_turn"] = randint(0,1)
                        self.send_to_others(client, reply)
                        reply["result"] = player.ready
                    case Action.RESET:
                        player.reset_request = not player.reset_request
                        self.reset_requests = 0
                        for p in self.players:
                            self.reset_requests += 1 if p.reset_request else 0
                        reply["result"] = player.reset_request
                        reply["reset_requests"] = self.reset_requests
                        reply["reset"] = self.reset_requests == 2
                        self.send_to_others(client, reply)
                        if self.reset_requests == 2:
                            self.reset_board()
                    case Action.EXITED:
                        self.disconect_client(client, player_id)

                self.send_data(client, reply)

            except TimeoutError:
                continue
            except Exception as e:
                print(f"Error: {e}")
                break
        self.disconect_client(client, player_id)

    def reset_board(self):
        self.players = [Player(), Player()]
        self.ready_players = 0
        self.match_started = False
        self.reset_requests = 0

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
                    print("---------------------")
                    print("All players connected")
                    print("---------------------")
                    break
            except TimeoutError:
                continue

        time.sleep(0.1)
        while self.pool:
            time.sleep(0.1)
        print("Server closed")
        self.server_socket.close()
        self.shutdown_request = False
        self.started = False

if __name__ == "__main__":
    server = GameServer()
    server.start_server()
