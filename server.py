import json
import socket
from _thread import *
from player import Player
import pickle

hostname = socket.gethostname()
server_ip = "10.59.61.151"
server_port = 5555

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_socket.bind((server_ip,server_port))
except socket.error as e:
    print(e)
server_socket.listen(2)

print(f"{hostname} started server at {server_ip}:{server_port}")

pool = []
names = {}
players = [Player(), Player()]
turn = 0
reseting = False

def connect_client(client):
    pool.append(client)
    names[client] = f"Player{len(pool)}"
    print(f"{names[client]} connected")

def disconect_client(client):
    pool.remove(client)
    client_name = names.pop(client)
    print(f"{client_name} disconnected")
    client.close()


def clientThred(client, address, player):
    global reseting
    global turn
    connect_client(client)
    print(f"{address} joined the game")
    client.send(pickle.dumps(players[player]))
    reply = ""
    while True:
        try:
            data = pickle.loads(client.recv(2048))
            if players[0].request_reset and players[1].request_reset:
                reseting = True
            if reseting:
                if not players[0].request_reset and not players[1].request_reset:
                    reseting = False
                players[0].restart()
                players[1].restart()
            else:
                players[player] = data

            if players[player].finished_turn:
                turn += 1
                players[player].my_turn = False
                players[player].finished_turn = False

            players[turn%2].my_turn = True



            if not data:
                print("Disconnected")
                break
            else:
                if player == 1:
                    reply = {
                    "p1" : players[1],
                    "p2" : players[0]}
                else:
                    reply = {
                    "p1" : players[0],
                    "p2" : players[1]}

                # print(f"Received: {data}")
                # print(f"Sending: {reply}")

            client.sendall(pickle.dumps(reply))
        except:
            break
    disconect_client(client)

current_player = 0
running = True
while running:
    client, address = server_socket.accept()
    print(f"connected to {address}")

    start_new_thread(clientThred, (client, address, current_player))
    current_player += 1
    if current_player >= 2:
        break

print("---------------------")
print("All players connected")
print("---------------------")
while running:
    if len(pool) <= 0:
        running = False
server_socket.close()
print("Server closed")
