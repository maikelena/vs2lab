import constRPC

from context import lab_channel

import itertools
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
        self._req_id_gen = itertools.count(1)
        self._pending = {}  # request_id -> callback
        self._pending_lock = threading.Lock()
        self._running = threading.Event()
        self._listener_thread = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')
        self._running.set()
        self._listener_thread = threading.Thread(target=self._listen, daemon=True)
        self._listener_thread.start()

    def stop(self):
        self._running.clear()
        self.chan.leave('client')

    def _listen(self):
        # Listen for ACK/RESULT messages and dispatch callbacks.
        while self._running.is_set():
            msgrcv = self.chan.receive_from(self.server, timeout=1)
            if msgrcv is None:
                continue

            _sender, payload = msgrcv
            if not isinstance(payload, tuple) or len(payload) < 2:
                continue

            msg_type = payload[0]
            req_id = payload[1]

            if msg_type == constRPC.ACK:
                # ACK received; client can continue doing other work.
                continue

            if msg_type == constRPC.RESULT and len(payload) >= 3:
                result = payload[2]
                cb = None
                with self._pending_lock:
                    cb = self._pending.pop(req_id, None)
                if cb is not None:
                    cb(result)

    def append_async(self, data, db_list, callback):
        assert isinstance(db_list, DBList)
        req_id = str(next(self._req_id_gen))
        with self._pending_lock:
            self._pending[req_id] = callback
        msglst = (constRPC.APPEND, req_id, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server
        return req_id

    def append(self, data, db_list):
        """
        Backwards-compatible sync wrapper around the async RPC.
        """
        done = threading.Event()
        holder = {}

        def _cb(result):
            holder['result'] = result
            done.set()

        self.append_async(data, db_list, _cb)
        done.wait()
        return holder['result']


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
                client = msgreq[0]  # see who is the caller
                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    req_id = msgrpc[1]
                    data = msgrpc[2]
                    db_list = msgrpc[3]

                    # ACK right away (async RPC)
                    self.chan.send_to({client}, (constRPC.ACK, req_id))

                    # Simulate long execution
                    time.sleep(10)

                    # Then send result
                    result = self.append(data, db_list)  # do local call
                    self.chan.send_to({client}, (constRPC.RESULT, req_id, result))
                else:
                    pass  # unsupported request, simply ignore
