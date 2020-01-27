import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json
import ast

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = ast.literal_eval(data.decode('utf-8'))
      print(str(addr) + " : " + str(data))
      if addr in clients:
         if 'message' in data and data['message'] == 'heartbeat':
             clients[addr]['lastBeat'] = datetime.now()
         if 'pos' in data:
             clients[addr]['pos'] = data['pos']
      else:
         if 'message' in data and data['message'] == 'connect':
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            pos = { "x" : random.uniform( 0.0, 5.0 ), "y": 0, "z": random.uniform( 0.0, 5.0 ) }
            clients[addr]['pos'] = pos
            
            for c in clients:
               if c is addr:
                  message = {"cmd": 0,"player":{"id":str(addr),"pos":pos}}
               else:
                  message = {"cmd": 1,"player":{"id":str(addr),"pos":pos}}
               m = json.dumps(message)
               print("new client: ", str(m), "cast to ", str(c)) 
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
               
            for c in clients:
                if c is not addr:
                    message = {"cmd": 1,"player":{"id":str(c), "pos":clients[c]['pos']}}
                    m = json.dumps(message)
                    print('old client: ', str(c), 'cast to ', str(addr))
                    sock.sendto(bytes(m,'utf8'), (addr[0],addr[1]))

def cleanClients(sock):
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
            message = {"cmd": 3, "player":{"id":str(c)}}
            m = json.dumps(message)
            for c in clients:
                sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 2, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['pos'] = clients[c]['pos']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print("game: ", s)
      for c in clients:
         print("client: ", str(c[0]), str(c[1]))
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
    main()
