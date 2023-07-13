import socket 
import threading
import os
import sys
import time
import datetime
from collections import defaultdict


class Server(object):
    ''' This is a Server class '''
    def __init__(self, HOST='', PORT=7734, V='P2P-Server'):
         # This function gets called whenever a new object is instantiated.
        self.HOST = HOST
        self.PORT = PORT
        self.V = V
        self.peers = defaultdict(set)
        self.rfcs = {}
        self.lock = threading.Lock() # declaring a lock
        self.CRED = '\033[91m'    # ANSI escape codes for colors
        self.CGREEN = '\33[32m'
        self.CYELLOW = '\33[33m'
        self.CBLUE = '\33[34m'
        self.CEND = '\033[0m'
        self.CBLINK = '\33[5m'


    def start(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET is for ipv4 address, SOCK_STREAM for TCP
            self.s.bind((self.HOST, self.PORT))
            self.s.listen(5)
            print(self.CBLUE + """
  
                                                           
""" + self.CEND)
            time.sleep(1)
            print(self.CGREEN + "Server %s is listening on port %s ..." % (self.V, self.PORT)  + self.CEND)
                     
            while True:
                clientsocket, address = self.s.accept()
                print('\n-------------------------------------------------------------------------------------------------')
                print(f"Connection from {address} has been established on",datetime.datetime.now())
                clientsocket.send(bytes("Connected to the Server.", "utf-8")) # utf-8 bytes used to send information to client
                thread = threading.Thread(target=self.handler, args=(clientsocket, address))
                thread.start()

        except KeyboardInterrupt:
            print(self.CRED + "\nShutting down the server..." + self.CEND)
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
                
    def handler(self, clientsocket, address):
        host = None
        port = None
        
        while True:
            try:
                request = clientsocket.recv(1024).decode()
                print("\nClient's request:\n%s" % request)
                lines = request.splitlines()
                method = lines[0].split()[0]
                #print("method: %s" % method)

                if method == 'Upload':
                    host = lines[1].split(None, 1)[1]
                    port = int(lines[2].split(None, 1)[1])
                    filename = lines[3].split(None, 1)[1]
                    self.addRecord(clientsocket, (host, port), filename)

                elif method == 'List':
                    self.getAllRecords(clientsocket)

                elif method == 'Download':
                    filename = lines[3].split(None, 1)[1]
                    self.getAllPeers(clientsocket, filename)

                else:
                    raise AttributeError(self.CRED + 'Method Did Not Matched!' + self.CEND)

            except ConnectionError:
                print(self.CRED + '\nClient %s:%s has left.' % (address[0], address[1]) + self.CEND)
                print('=================================================================================================')
                

                # cleaning the data in the server
                if host and port:
                    self.clear(host,port)
                    
                clientsocket.close()
                break

            except BaseException:
                try:
                    clientsocket.sendall(str.encode(self.CRED + '\n400 Bad Request.' + self.CEND))
                except ConnectionError:
                    print(self.CRED + '\nClient %s:%s has left.' % (address[0], address[1]) + self.CEND)
                    print('=================================================================================================')

                    # cleaning the data in the server
                    if host and port:
                        self.clear(host,port)
                        
                    clientsocket.close()
                    break

    def clear(self, host, port):
        self.lock.acquire() 
        self.peers.pop((host, port), None)
        self.lock.release()


    def addRecord(self, clientsocket, peer, filename):
        self.lock.acquire() # to write updated value to the shared variable
        try:
            self.peers[peer].add(filename) # adding the value 'filename' in the key 'peer'
            self.rfcs.setdefault(filename, set()).add(peer)
        finally:
            self.lock.release()

        header = self.V + ' 200 OK\n'
        header += 'File %s uploaded from %s %s\n' % (filename, peer[0], peer[1])
        clientsocket.sendall(str.encode(self.CGREEN + header + self.CEND))  


    def getAllRecords(self, clientsocket):
        self.lock.acquire()
        try:
            if not self.rfcs:
                header = self.V + ' 404 File Not Found\n'
                clientsocket.sendall(str.encode(self.CRED + header + self.CEND))

            else:
                header = self.V + ' 200 OK\n'
                header += '\nAvailable Files:\n'
                for filename in self.rfcs:
                    # filename = next(iter(self.rfcs))
                    allpeer = next(iter(self.rfcs.values()))
                    # allpeer = next(iter(next(iter(self.rfcs.values()))))
                    for peer in allpeer:
                        header += 'File %s in %s %s\n' % (filename, peer[0], peer[1])
            
                clientsocket.sendall(str.encode(self.CGREEN + header + self.CEND))

        finally:
            self.lock.release()

    def getAllPeers(self, clientsocket, filename):
        self.lock.acquire()
        try:
            if filename not in self.rfcs:
                header = self.V + ' 404 File Not Found\n'
                clientsocket.sendall(str.encode(self.CRED + header + self.CEND))

            else:
                header = self.V + ' 200 OK\n'
                # filename = next(iter(self.rfcs))
                allpeer = next(iter(self.rfcs.values()))
                for peer in allpeer:
                    header += 'File %s in %s %s\n' % (filename, peer[0], peer[1])
            
                clientsocket.sendall(str.encode(header))

        finally:
            self.lock.release()
      


if __name__ == '__main__':

    Server().start()
        
    
