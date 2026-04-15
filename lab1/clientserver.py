"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

# init loging channels for the lab
lab_logging.setup(stream_level=logging.INFO)

# pylint: disable=logging-not-lazy, line-too-long


class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # prevents errors due to "addresses in use"
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))
        self.phonebook = {
            "Alice": "12345",
            "Bob": "67890",
            "Charlie": "55555",
            "David": "54321",
            "Eve": "98765",
            "Frank": "11111",
        }

    def get(self, name):
        """Return number for a given name or None."""
        return self.phonebook.get(name)

    def getall(self):
        """Return the complete phonebook."""
        return self.phonebook

    def handle_request(self, request):
        """Parse and process one request string."""
        request = request.strip()

        if request == "GETALL":
            entries = [f"{name}:{number}" for name,
                       number in self.getall().items()]
            return "OKALL|" + ";".join(entries)

        parts = request.split("|")
        command = parts[0]

        if command == "GET" and len(parts) == 2:
            name = parts[1]
            number = self.get(name)
            if number is None:
                return "ERROR|NOTFOUND"
            return f"OK|{name}|{number}"

        return "ERROR|BAD_REQUEST"

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        self._logger.info("Server listening on %s:%s",
                          const_cs.HOST, const_cs.PORT)

        # as long as _serving (checked after connections or socket timeouts)
        while self._serving:
            try:
                # pylint: disable=unused-variable
                # returns new socket and address of client
                (connection, address) = self.sock.accept()
                self._logger.info("Accepted connection from %s", address)

                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        self._logger.info("Client closed connection")
                        break  # stop if client stopped

                    request = data.decode("utf-8")
                    self._logger.info("Received request: %s", request)

                    response = self.handle_request(request)
                    self._logger.info("Sending response: %s", response)

                    connection.send(response.encode("utf-8"))

                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")

    def stop(self):
        """Stop server loop."""
        self._serving = False


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def _send_request(self, request):
        """Send one request and return decoded response."""
        self.logger.info("Sending request: %s", request)
        self.sock.send(request.encode("utf-8"))
        data = self.sock.recv(1024)
        response = data.decode("utf-8")
        self.logger.info("Received response: %s", response)
        return response

    def get(self, name):
        """Request one entry by name."""
        return self._send_request(f"GET|{name}")

    def getall(self):
        """Request all entries."""
        return self._send_request("GETALL")

    def call(self, msg_in="Hello, world"):
        """ Call server """
        self.sock.send(msg_in.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii')
        print(msg_out)  # print the result
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return msg_out

    def close(self):
        """ Close socket """
        self.sock.close()
