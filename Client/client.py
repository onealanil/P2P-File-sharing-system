import socket
import os
import sys
import time
import threading
from pathlib import Path
import mimetypes
import platform
from cryptography.fernet import Fernet

class Client(object):
    '''This is a client class'''
    def __init__(self, serverhost='localhost', V='P2P-REWANTA', DIR='Downloads'): #server host is localhost by default
        self.SERVER_HOST = serverhost
        self.SERVER_PORT = 7734
        self.V = V
        # self.DIR = 'Files'
        # Path(self.DIR).mkdir(exist_ok=True)
        self.UPLOAD_PORT = None
        self.shareable = True
        self.CRED = '\033[91m'    # ANSI escape codes for colors
        self.CGREEN = '\33[32m'
        self.CYELLOW = '\33[33m'
        self.CBLUE = '\33[34m'
        self.CEND = '\033[0m'


    def start(self):
        '''To connect to server'''
        print(self.CBLUE + """

                                                           
""" + self.CEND)

        message1 = 'Connecting to the server %s:%s \n\n' % (self.SERVER_HOST, self.SERVER_PORT)
        for char in message1:
            sys.stdout.write(self.CYELLOW + char + self.CEND)
            sys.stdout.flush()
            time.sleep(0.01)
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET is for ipv4 address, SOCK_STREAM for TCP
        try:
            self.server.connect((self.SERVER_HOST, self.SERVER_PORT))
            msg = self.server.recv(1024)
            print(self.CGREEN + msg.decode() + self.CEND)
        except Exception:
            print(self.CRED + 'Server Not Available!' + self.CEND)
            time.sleep(0.5)
            print(self.CRED + '\nShutting down the system...' + self.CEND)
            time.sleep(1)
            return

        uploader_process = threading.Thread(target=self.init_upload)
        uploader_process.start()

        while self.UPLOAD_PORT is None:
            # wait until upload port is initialized
            pass

        message2 = '\nListening on the upload port: %s\n' % self.UPLOAD_PORT
        for char in message2:
            sys.stdout.write(self.CYELLOW + char + self.CEND)
            sys.stdout.flush()
            time.sleep(0.01)

        self.cli()


    def cli(self):
        '''For users to choose their options'''
        choose = {'1': self.upload, '2': self.listall, '3': self.pre_download, '4': self.decrypt, '5': self.shutdown} # Dictionary to store data values

        while True:
            try:
                print('\n*************************************************************************')
                request = input('\n1: Upload Files \n2: List All Available Files \n3: Download Files \n4: Decrypt File \n5: Shut Down \n\nEnter your request: ')
                choose.setdefault(request, self.invalid_input)() # to set default value to 'request'
            except Exception:
                print(self.CRED + '\nSystem Error.'+ self.CEND)
            except BaseException:
                self.shutdown()


    def init_upload(self):
        '''To listen the upload port'''
        self.uploader = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.uploader.bind(('', 0)) # 0 is reserved port in TCP/IP
        self.UPLOAD_PORT = self.uploader.getsockname()[1] # To get the socket port number as the second element of 'getsockname' is socket port number
        self.uploader.listen(5)

        while self.shareable is True:
            conn, address = self.uploader.accept() # .accept() contains tuple of new host and the remote address
            handler = threading.Thread(target=self.handle_upload, args=(conn, address))
            handler.start()
        
        self.uploader.close()


    def handle_upload(self, clientsocket, address):
        header = clientsocket.recv(1024).decode().splitlines() # .recv() function is to receive message from socket, .decode to decode the message and .splitlines to split string into list
        try:
            method = header[0].split()[0]
            filename = header[0].split()[-1]
            path = '%s.txt' % filename
            # path = '%s/%s.txt' % (self.DIR, filename)
                
            if not Path(path).is_file():
                clientsocket.sendall(str.encode('404 File Not Found!!!\n')) # .encode convert strings to bytes

            elif method == 'Download':
                header = self.V + ' 200 OK\n'
                header += 'Date: %s\n' % (time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))
                header += 'OS: %s\n' % (platform.platform())
                header += 'Last-Modified: %s\n' % (time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(os.path.getmtime(path))))
                header += 'Content-Length: %s\n' % (os.path.getsize(path))
                header += 'Content-Type: %s\n' % (mimetypes.MimeTypes().guess_type(path)[0])
                clientsocket.sendall(header.encode())

                send_length = 0
                with open(path, 'r') as file:
                    to_send = file.read(1024)
                    while to_send:
                        send_length += len(to_send.encode())
                        clientsocket.sendall(to_send.encode())
                        to_send = file.read(1024)
            
            else:
                print(self.CRED + 'Bad Request.. \nPlease try again!' + self.CEND)
            
        except Exception:
            clientsocket.sendall(str.encode(self.V + '\n400 Bad Request'))
        
        finally:
            clientsocket.close()


    def write_key(self, filename):
        """Generating a new random key and saving it into a file"""
        key = Fernet.generate_key() # generated key is a bytes object of base64 encoded string
        with open(filename+'key.key', 'wb') as key_file:
            key_file.write(key)

    def load_key(self, filename):
        """Loads the key from the current directory named key.key"""
        return open(filename+'key.key', 'rb').read()


    def encrypt(self, file, key):
        """It encrypts the file and write it"""
        fernet = Fernet(key)

        with open(file, 'rb') as f:
            # read all file data
            file_data = f.read()
        
        encrypted_data = fernet.encrypt(file_data)

        with open(file, 'wb') as f:
            # write the encrypted file
            f.write(encrypted_data)


    def upload(self, filename=None):
        # To upload the files
        print(self.CYELLOW + '\nNote: Please upload the copy of file you want to upload.' + self.CEND) 
        filename = input('Enter the file name: ')
        file = Path('%s.txt' % filename)
        # file = Path('%s/%s.txt' % (self.DIR, filename))

        if not file.is_file():
            print(self.CRED + '\nFile Do Not Exist! Upload the file that is in your computer.' + self.CEND)
        
        elif file.is_file():
            self.write_key(filename)
            key = self.load_key(filename)
            new_file = '%s.txt' % filename
            self.encrypt(new_file, key)

            print(self.CGREEN + '\nUploading...' + self.CEND)
            print(self.CGREEN + 'Uploading Completed!' + self.CEND)
            msg = 'Upload File\n'
            msg += 'Host: %s\n' % socket.gethostname()
            msg += 'Port: %s\n' % self.UPLOAD_PORT
            msg += 'Filename: %s\n' % filename
            self.server.sendall(msg.encode())
            res = self.server.recv(1024).decode()
            print('\nServer response: \n%s' % res)

        else:
            print(self.CRED + '\nUploading Failed!' + self.CEND)

        
    def listall(self):
        l1 = 'List All Available File\n'
        l2 = 'Host: %s\n' % socket.gethostname()
        l3 = 'Port: %s\n' % self.UPLOAD_PORT
        msg = l1 + l2 + l3
        self.server.sendall(msg.encode())
        res = self.server.recv(1024).decode()
        print('\nServer response: \n%s' % res)
        
    def pre_download(self):
        filename = input('\nEnter the name of the file you want to download: ')
        msg = 'Download Request\n'
        msg += 'Host: %s\n' % socket.gethostname()
        msg += 'Port: %s\n' % self.UPLOAD_PORT
        msg += 'Filename: %s\n' % filename
        msg += 'OS: %s\n' % platform.platform()
        self.server.sendall(msg.encode())
        lines = self.server.recv(1024).decode().splitlines()
        
        if lines[0].split()[1] == '200':
            print('\nAvailable peers:\n ')
            
            for i, line in enumerate(lines[1:]):
                line = line.split()
                print(self.CGREEN + '%s: %s:%s' % (i + 1, line[-2], line[-1]) + self.CEND)
                
            try:
                peer = int(input('\nChoose one peer to download: '))
                filename = lines[peer].split()[1]
                peer_host = lines[peer].split()[-2]
                peer_port = int(lines[peer].split()[-1])
            except Exception:
                print(self.CRED + 'Invalid Input!' + self.CEND)
            if((peer_host, peer_port) == (socket.gethostname(), self.UPLOAD_PORT)):
                print(self.CRED + 'You cannot choose yourself as peer.' + self.CEND)
                self.cli()
            self.download(filename, peer_host, peer_port)
            
        elif lines[0].split()[1] == '400':
            print(self.CRED + 'Invalid Input.' + self.CEND)

        elif lines[0].split()[1] == '404':
            print(self.CRED + '\nFile Not Available!' + self.CEND)


    def decrypt(self, filename_dec=None):
        """It decrypts the file and write it"""
        filename_dec = input('\nEnter the file name you want to decrypt: ') 
        file = Path('%s.txt' % filename_dec)
     
        if not file.is_file():
            print(self.CRED + '\nFile Do Not Exist! Upload the file that you had downloaded.' + self.CEND)

        elif file.is_file():
            key = self.load_key(filename_dec)
            key_path = Path('%skey.key' % filename_dec)
            if not key_path.is_file:
                print(self.CRED + '\nYou do not have key to decrypt the file.' + self.CEND)
            elif key_path.is_file:
                fernet = Fernet(key)
                filename_decr = '%s.txt' % filename_dec
                with open(filename_decr, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = fernet.decrypt(encrypted_data)

                with open(filename_decr, 'wb') as f:
                    # write the decrypted file
                    f.write(decrypted_data)

                print(self.CGREEN + '\nSuccessfully Decrypted!' + self.CEND)

            else:
                print(self.CRED + '\nUnable to decrypt the file!' + self.CEND)
                
    def download(self, filename, peer_host, peer_port):
        try:
            clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if clientsocket.connect_ex((peer_host, peer_port)): # returns 0 if successful
                print(self.CRED + 'No any peer available! ' + self.CEND)

            msg = 'Download Request for file %s\n' % filename
            msg += 'Host: %s\n' % socket.gethostname()
            msg += 'Port: %s\n' % self.UPLOAD_PORT
            msg += 'OS: %s\n' % platform.platform()
            clientsocket.sendall(msg.encode())

            header = clientsocket.recv(1024).decode()
            print('\nRecieve response: \n%s' % header)
            header = header.splitlines()

            if header[0].split()[-2] == '200':
                # path = '%s/%s.txt' % (self.DIR, filename)
                path = '%s.txt' % filename

                print(self.CGREEN + 'Downloading...' + self.CEND)
                time.sleep(0.5)
                try:
                    with open(path, 'w') as file:
                        content = clientsocket.recv(1024)
                        while content:
                            file.write(content.decode())
                            content = clientsocket.recv(1024)
                except Exception:
                    print(self.CRED + 'Downloading Failed!' + self.CEND)

                total_length = int(header[4].split()[1])

                if os.path.getsize(path) < total_length:
                    print(self.CRED + 'Downloading Failed!' + self.CEND)

                print(self.CGREEN + 'Downloading Completed!' + self.CEND)
                print(self.CYELLOW + '\nThe downloaded file is encrypted.')
                print('To decrypt the file, store the key in the file directory and use this system.' + self.CEND)

            elif header[0].split()[1] == '400':
                print(self.CRED + '\nInvalid Input.' + self.CEND)
                 
            elif header[0].split()[1] == '404':
                print(self.CRED + '\nFile Not Available!' + self.CEND)
            
        finally:
            clientsocket.close()

    def invalid_input(self):
        print(self.CRED + '\nInvalid Input. Please try again!' + self.CEND)

    def shutdown(self):
        print(self.CRED + '\nShutting down the system...' + self.CEND)
        time.sleep(1)
        self.server.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__':

    if len(sys.argv) == 2:
        client = Client(sys.argv[1]) 

    else:
        client = Client()

    client.start()
    
