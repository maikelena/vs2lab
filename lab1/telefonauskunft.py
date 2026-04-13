"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self.phonebook = {
            "Chloe": "111",
            "Maike": "222",
            "Romy": "333"
        }
        self._logger.info("Server bound to socket " + str(self.sock))

    def get(self, name):
        return self.phonebook.get(name)

    def getAll(self):
        return self.phonebook
    
    def handler(self, request):
        self._logger.info("Server received request: %s", request)
        if request.startswith("GET|"):
            name = request.split("|", 1)[1]
            number = self.get(name)
            if number is None:
                return "ERROR|NOTFOUND"
            return f"OK|{name}|{number}"

        if request == "GETALL":
            entries = [f"{name}={number}" for name, number in self.getall().items()]
            return "OKALL|" + ";".join(entries)

        return "ERROR|BAD_REQUEST"

    def serve(self):
        """ Serve """
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        break  # stop if client stopped
                    request = data.decode("ascii")
                    response = self.handler(request)
                    connection.send(response.encode("ascii"))
                    self._logger.info("Server sent response: %s", response)
                connection.close()  # close the connection

            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call(self, request):
        """ Call server """
        self.sock.send(request.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        response = data.decode('ascii')
        self.sock.close()
        self.logger.info("Client down.")
        return response
    
    def get(self, name):
        """API operation GET(name)"""
        return self.call(f"GET|{name}")

    def getall(self):
        """API operation GETALL()"""
        return self.call("GETALL")

    def close(self):
        """ Close socket """
        self.sock.close()
