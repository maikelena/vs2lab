import logging

import stablelog

# coordinator messages
from const3PC import VOTE_REQUEST, PREPARE_COMMIT, GLOBAL_COMMIT, GLOBAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT, READY_COMMIT
# misc constants
from const3PC import TIMEOUT


class Coordinator:
    """
    Minimal centralized Three-Phase Commit (3PC) coordinator.
    Implements only the basic protocol flow (no termination protocols).
    """

    def __init__(self, chan):
        self.channel = chan
        self.coordinator = self.channel.join('coordinator')
        self.participants = set()
        self.stable_log = stablelog.create_log("coordinator-" + self.coordinator)
        self.logger = logging.getLogger("vs2lab.lab6.3pc.Coordinator")
        self.state = None

    def _enter_state(self, state):
        self.stable_log.info(state)
        self.logger.info("Coordinator {} entered state {}."
                         .format(self.coordinator, state))
        self.state = state

    def init(self):
        self.channel.bind(self.coordinator)
        self._enter_state('INIT')
        self.participants = self.channel.subgroup('participant')

    def run(self):
        # Phase 1a: vote request
        self._enter_state('WAIT')
        self.channel.send_to(self.participants, VOTE_REQUEST)

        # Phase 2a: collect votes
        yet_to_receive = set(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)
            if (not msg) or (msg[1] == VOTE_ABORT):
                reason = "timeout" if not msg else "local_abort from " + msg[0]
                self._enter_state('ABORT')
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return "Coordinator {} terminated in state ABORT. Reason: {}.".format(
                    self.coordinator, reason
                )

            assert msg[1] == VOTE_COMMIT
            yet_to_receive.remove(msg[0])

        # Phase 2a -> PRECOMMIT
        self._enter_state('PRECOMMIT')
        self.channel.send_to(self.participants, PREPARE_COMMIT)

        # Phase 3a: collect READY_COMMIT
        yet_to_receive = set(self.participants)
        while len(yet_to_receive) > 0:
            msg = self.channel.receive_from(self.participants, TIMEOUT)
            if not msg:
                self._enter_state('ABORT')
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return "Coordinator {} terminated in state ABORT. Reason: timeout.".format(
                    self.coordinator
                )

            if msg[1] != READY_COMMIT:
                self._enter_state('ABORT')
                self.channel.send_to(self.participants, GLOBAL_ABORT)
                return "Coordinator {} terminated in state ABORT. Reason: unexpected message {} from {}.".format(
                    self.coordinator, msg[1], msg[0]
                )

            yet_to_receive.remove(msg[0])

        # Phase 3a -> COMMIT
        self._enter_state('COMMIT')
        self.channel.send_to(self.participants, GLOBAL_COMMIT)
        return "Coordinator {} terminated in state COMMIT.".format(self.coordinator)

