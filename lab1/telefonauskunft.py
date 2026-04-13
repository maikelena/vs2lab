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
        self._logger.info("Server connected to socket " + str(self.sock))

    def get(self, name):
        """Return number for a given name or None."""
        return self.phonebook.get(name)

    def getAll(self):
        """Return all phonebook entries."""
        return self.phonebook
    
    def handle(self, request):
        self._logger.info("Server received request: " + request)
        if request.startswith("GET|"):
            name = request.split("|", 1)[1]
            number = self.get(name)
            if number is None:
                return "ERROR|NOTFOUND"
            return f"OK|{name}|{number}"

        if request == "GETALL":
            entries = [f"{name}={number}" for name, number in self.getAll().items()]
            return "OKALL|" + ";".join(entries)
        
        return "ERROR|BAD_REQUEST"

    def serve(self):
        """ Serve """
        self.sock.listen(1)
        self._logger.info("Server listening on %s:%s", const_cs.HOST, const_cs.PORT)

        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client

                    if not data:
                        self._logger.info("Client closed connection")
                        break  # stop if client stopped

                    request = data.decode("ascii")
                    self._logger.info("Received request: %s", request)
                    response = self.handle(request)
                    connection.send(response.encode("ascii"))
                    self._logger.info("Server sent response: " + response)

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
        self.logger.info("Sending request: " + request)
        self.sock.send(request.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        response = data.decode('ascii')
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
