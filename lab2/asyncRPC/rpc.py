import constRPC

from context import lab_channel

import threading
import time


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        self.chan.leave('client')

    def wait(self, callback):
        msgrcv = self.chan.receive_from(self.server)

        if msgrcv is not None:
            payload = msgrcv[1]
            if payload[0] == "RESULT":
                callback(payload[1])

    def append(self, data, db_list, callback):
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server

        ack = self.chan.receive_from(self.server)
        if ack is not None and ack[1][0] == "ACK":
            print("ACK received, continuing with other work...")

        result_thread = threading.Thread(target=self.wait, args=(callback,))
        result_thread.start()
        return result_thread

class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                print("Request received")
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    self.chan.send_to({client}, ("ACK", constRPC.APPEND))
                    print("ACK sent")

                    time.sleep(10)  # simulate operation

                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    self.chan.send_to({client}, ("RESULT", result))  # return response
                    print("Result send")
                else:
                    pass  # unsupported request, simply ignore
