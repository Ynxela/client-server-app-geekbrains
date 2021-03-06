import logging
import select
import threading
from argparse import ArgumentParser
from socket import socket

import yaml

from handlers import handle_default_request

parser = ArgumentParser()
parser.add_argument(
    '-c', '--config', type=str,
    required=False, help='Sets config file path'
)

args = parser.parse_args()

default_config = {'host': 'localhost',
                  'port': 1080,
                  'buffersize': 1024
                  }

if args.config:
    with open(args.config) as file:
        config = yaml.load(file, Loader=yaml.Loader)
        default_config.update(default_config)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class Server:
    def __init__(self, host, port, buffersize, handler):
        self._b_requests_list = []
        self._connections = []
        self._handler = handler
        self._host = host
        self._port = port
        self._buffersize = buffersize
        self._socket = socket()

    def bind(self, backlog=5):
        self._socket.bind((self._host, self._port))
        self._socket.settimeout(0)
        self._socket.listen(backlog)

    def accept(self):
        try:
            client, address = self._socket.accept()
        except:
            pass
        else:
            self._connections.append(client)
            logging.info(
                'client was connected with {}:{} | Connections: {}'.format(address[0], address[1],
                                                                           self._connections))

    def read(self, sock):
        try:
            b_request = sock.recv(self._buffersize)
        except:
            self._connections.remove(sock)
        else:
            if b_request:
                self._b_requests_list.append(b_request)

    def write(self, sock, response):
        try:
            sock.send(response)
        except:
            self._connections.remove(sock)

    def run(self):
        try:
            logging.info('server was started with {}:{}'.format(self._host, self._port))

            while True:
                self.accept()

                rlist, wlist, xlist = select.select(self._connections, self._connections, self._connections, 0)

                for r_client in rlist:
                    r_thread = threading.Thread(target=self.read, args=(r_client, ))
                    r_thread.start()

                if self._b_requests_list:
                    b_request = self._b_requests_list.pop()
                    b_response = self._handler(b_request)

                    for w_client in wlist:
                        w_thread = threading.Thread(target=self.write, args=(w_client, b_response))
                        w_thread.start()

        except KeyboardInterrupt:
            logging.info('server shutdown')


if __name__ == '__main__':
    server = Server(default_config.get('host'), default_config.get('port'), default_config.get('buffersize'),
                    handle_default_request)
    server.bind()
    server.run()
