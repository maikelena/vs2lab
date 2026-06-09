import logging
import random
import time

from constMutex import (
    ACTIVE,
    ALLOW,
    ENTER,
    FAILURE_TIMEOUT,
    HEARTBEAT,
    HEARTBEAT_INTERVAL,
    RECEIVE_TIMEOUT,
    RELEASE,
)


class Process:
    """
    Implements access management to a critical section (CS) via fully
    distributed mutual exclusion (MUTEX).

    Processes broadcast messages (ENTER, ALLOW, RELEASE, HEARTBEAT)
    timestamped with logical (lamport) clocks. Mutex messages are stored in
    local queues sorted by logical clock time. Heartbeats are only used for
    detecting crashed processes.

    Processes follow different behavioral patterns. An ACTIVE process competes
    with others for accessing the critical section. A PASSIVE process will never
    request to enter the critical section itself but will allow others to do so.

    A process broadcasts an ENTER request if it wants to enter the CS. A process
    that doesn't want to ENTER replies with an ALLOW broadcast. A process that
    wants to ENTER and receives another ENTER request replies with an ALLOW
    broadcast (which is then later in time than its own ENTER request).

    A process enters the CS if a) its ENTER message is first in the queue (it is
    the oldest pending message) AND b) all other processes have sent messages
    that are younger (either ENTER or ALLOW). RELEASE requests purge
    corresponding ENTER requests from the top of the local queues.

    Message Format:

    <Message>: (Timestamp, Process_ID, <Request_Type>)

    <Request Type>: ENTER | ALLOW | RELEASE | HEARTBEAT

    """

    def __init__(self, chan):
        self.channel = chan  # Create ref to actual channel
        self.process_id = self.channel.join('proc')  # Find out who you are
        self.all_processes: list = []  # All procs in the proc group
        self.other_processes: list = []  # Needed to multicast to others
        self.queue = []  # The request queue list
        self.clock = 0  # The current logical clock
        self.peer_name = 'unassigned'  # The original peer name
        self.peer_type = 'unassigned'  # A flag indicating behavior pattern
        self.last_seen = {}  # Last observed activity per other process
        self.last_heartbeat = 0.0  # Last heartbeat sent by this process
        self.failed_processes = set()  # Peers already reported as crashed
        self.logger = logging.getLogger("vs2lab.lab5.mutex.process.Process")

    def __mapid(self, id='-1'):
        # format channel member address
        if id == '-1':
            id = self.process_id
        return 'Proc-'+str(id)

    def __cleanup_queue(self):
        if len(self.queue) > 0:
            self.queue.sort()
            # There should never be old ALLOW messages at the head of the queue
            while self.queue[0][2] == ALLOW:
                del (self.queue[0])
                if len(self.queue) == 0:
                    break

    def __request_to_enter(self):
        self.clock = self.clock + 1  # Increment clock value
        request_msg = (self.clock, self.process_id, ENTER)
        self.queue.append(request_msg)  # Append request to queue
        self.__cleanup_queue()  # Sort the queue
        self.channel.send_to(self.other_processes, request_msg)  # Send request

    def __allow_to_enter(self, requester):
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, ALLOW)
        self.channel.send_to([requester], msg)  # Permit other

    def __send_heartbeat(self, now):
        if now - self.last_heartbeat < HEARTBEAT_INTERVAL:
            return

        self.clock = self.clock + 1
        msg = (self.clock, self.process_id, HEARTBEAT)
        self.channel.send_to(self.other_processes, msg)
        self.last_heartbeat = now
        self.logger.debug("{} sent HEARTBEAT to {}.".format(
            self.__mapid(),
            list(map(self.__mapid, self.other_processes))))

    def __remove_failed_process(self, process_id, silent_for):
        if process_id in self.failed_processes:
            return

        self.failed_processes.add(process_id)
        self.all_processes = [
            proc for proc in self.all_processes if proc != process_id]
        self.other_processes = [
            proc for proc in self.other_processes if proc != process_id]
        self.last_seen.pop(process_id, None)

        old_queue_length = len(self.queue)
        self.queue = [msg for msg in self.queue if msg[1] != process_id]
        removed_messages = old_queue_length - len(self.queue)
        self.__cleanup_queue()

        self.logger.warning(
            "{} detected crashed process {} after {:.1f} seconds without "
            "activity.".format(
                self.__mapid(), self.__mapid(process_id), silent_for))
        self.logger.info(
            "{} removed {} queue entries for {}. Remaining processes: {}."
            .format(
                self.__mapid(),
                removed_messages,
                self.__mapid(process_id),
                list(map(self.__mapid, self.all_processes))))

    def __check_for_failures(self, now):
        failed = [
            (process_id, now - last_activity)
            for process_id, last_activity in list(self.last_seen.items())
            if now - last_activity >= FAILURE_TIMEOUT
        ]
        for process_id, silent_for in failed:
            self.__remove_failed_process(process_id, silent_for)

    def __maintenance(self):
        now = time.monotonic()
        self.__send_heartbeat(now)
        self.__check_for_failures(now)

    def __release(self):
        # need to be first in queue to issue a release
        assert self.queue[0][1] == self.process_id, 'State error: inconsistent local RELEASE'

        # construct new queue from later ENTER requests (removing all ALLOWS)
        tmp = [r for r in self.queue[1:] if r[2] == ENTER]
        self.queue = tmp  # and copy to new queue
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, RELEASE)
        # Multicast release notification
        self.channel.send_to(self.other_processes, msg)

    def __allowed_to_enter(self):
        if not self.queue:
            return False

        # See who has sent a message (the set will hold at most one element per sender)
        processes_with_later_message = set([req[1] for req in self.queue[1:]])
        # Access granted if this process is first in queue and all others have answered (logically) later
        first_in_queue = self.queue[0][1] == self.process_id
        all_have_answered = set(self.other_processes).issubset(
            processes_with_later_message)
        return first_in_queue and all_have_answered

    def __receive(self):
        if not self.other_processes:
            return

        # Pick up any message
        received = self.channel.receive_from(
            self.other_processes, RECEIVE_TIMEOUT)
        if received:
            sender, msg = received
            self.last_seen[sender] = time.monotonic()

            self.clock = max(self.clock, msg[0])  # Adjust clock value...
            self.clock = self.clock + 1  # ...and increment

            self.logger.debug("{} received {} from {}.".format(
                self.__mapid(),
                "ENTER" if msg[2] == ENTER
                else "ALLOW" if msg[2] == ALLOW
                else "RELEASE" if msg[2] == RELEASE
                else "HEARTBEAT", self.__mapid(msg[1])))

            if msg[2] == ENTER:
                self.queue.append(msg)  # Append an ENTER request
                # and unconditionally allow (don't want to access CS oneself)
                self.__allow_to_enter(msg[1])
            elif msg[2] == ALLOW:
                self.queue.append(msg)  # Append an ALLOW
            elif msg[2] == RELEASE:
                # assure release requester indeed has access (his ENTER is first in queue)
                assert self.queue[0][1] == msg[1] and self.queue[0][2] == ENTER, 'State error: inconsistent remote RELEASE'
                del (self.queue[0])  # Just remove first message
            elif msg[2] == HEARTBEAT:
                pass

            self.__cleanup_queue()  # Finally sort and cleanup the queue
        else:
            self.logger.debug("{} timed out on RECEIVE. Local queue: {}".
                              format(self.__mapid(),
                                     list(map(lambda msg: (
                                         'Clock '+str(msg[0]),
                                         self.__mapid(msg[1]),
                                         msg[2]), self.queue))))

    def init(self, peer_name, peer_type):
        self.channel.bind(self.process_id)

        self.all_processes = list(self.channel.subgroup('proc'))
        # sort string elements by numerical order
        self.all_processes.sort(key=lambda x: int(x))

        self.other_processes = list(self.channel.subgroup('proc'))
        self.other_processes.remove(self.process_id)
        self.other_processes.sort(key=lambda x: int(x))

        self.peer_name = peer_name  # assign peer name
        self.peer_type = peer_type  # assign peer behavior
        now = time.monotonic()
        self.last_seen = {
            process_id: now for process_id in self.other_processes}
        self.last_heartbeat = now - HEARTBEAT_INTERVAL

        self.logger.info("{} joined channel as {}.".format(
            peer_name, self.__mapid()))

    def run(self):
        while True:
            self.__maintenance()

            # Enter the critical section if
            # 1) there are more than one process left and
            # 2) this peer has active behavior and
            # 3) random is true
            if len(self.all_processes) > 1 and \
                    self.peer_type == ACTIVE and \
                    random.choice([True, False]):
                self.logger.debug("{} wants to ENTER CS at CLOCK {}."
                                  .format(self.__mapid(), self.clock))

                self.__request_to_enter()
                while not self.__allowed_to_enter():
                    self.__receive()
                    self.__maintenance()

                # Stay in CS for some time ...
                sleep_time = random.randint(0, 2000)
                self.logger.debug("{} enters CS for {} milliseconds."
                                  .format(self.__mapid(), sleep_time))
                print(" CS <- {}".format(self.__mapid()))
                time.sleep(sleep_time/1000)

                # ... then leave CS
                print(" CS -> {}".format(self.__mapid()))
                self.__release()
                continue

            # Occasionally serve requests to enter
            if random.choice([True, False]):
                self.__receive()
