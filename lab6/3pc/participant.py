import random
import logging

# coordinator messages
from const3PC import VOTE_REQUEST, PREPARE_COMMIT, GLOBAL_COMMIT, GLOBAL_ABORT
# participant decisions
from const3PC import LOCAL_SUCCESS, LOCAL_ABORT
# participant messages
from const3PC import VOTE_COMMIT, VOTE_ABORT, READY_COMMIT
# misc constants
from const3PC import TIMEOUT

import stablelog


class Participant:

    def __init__(self, chan):
        self.channel = chan
        self.participant = self.channel.join('participant')
        self.stable_log = stablelog.create_log("participant-" + self.participant)
        self.logger = logging.getLogger("vs2lab.lab6.3pc.Participant")
        self.coordinator = {}
        self.all_participants = {}
        self.state = 'NEW'

    @staticmethod
    def _do_work():
        # Simulate local activities that may succeed or not
        return LOCAL_ABORT if random.random() > 2/3 else LOCAL_SUCCESS

    def _enter_state(self, state):
        self.stable_log.info(state)
        self.logger.info("Participant {} entered state {}."
                         .format(self.participant, state))
        self.state = state

    def init(self):
        self.channel.bind(self.participant)
        self.coordinator = self.channel.subgroup('coordinator')
        self.all_participants = self.channel.subgroup('participant')
        self._enter_state('INIT')

    def _new_coordinator_id(self):
        return min(self.all_participants, key=int)

    def _terminate_after_coordinator_crash(self):
        p_k = self._new_coordinator_id()

        if self.participant == p_k:
            if self.state == 'READY':
                self._enter_state('ABORT')
                self.channel.send_to(self.all_participants, GLOBAL_ABORT)
                return GLOBAL_ABORT
            if self.state == 'PRECOMMIT':
                self._enter_state('COMMIT')
                self.channel.send_to(self.all_participants, GLOBAL_COMMIT)
                return GLOBAL_COMMIT
            if self.state == 'COMMIT':
                self.channel.send_to(self.all_participants, GLOBAL_COMMIT)
                return GLOBAL_COMMIT
            if self.state == 'ABORT':
                self.channel.send_to(self.all_participants, GLOBAL_ABORT)
                return GLOBAL_ABORT
            return GLOBAL_ABORT

        msg = self.channel.receive_from({p_k}, TIMEOUT)
        if not msg:
            self._enter_state('ABORT')
            return GLOBAL_ABORT

        decision = msg[1]
        if decision == GLOBAL_COMMIT:
            self._enter_state('COMMIT')
        else:
            self._enter_state('ABORT')
        return decision

    def run(self):
        # Phase 1b: wait for vote request
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        if not msg:
            self._enter_state('ABORT')
            return "Participant {} terminated in state ABORT due to timeout.".format(
                self.participant
            )

        assert msg[1] == VOTE_REQUEST

        # local decision
        decision = self._do_work()
        if decision == LOCAL_ABORT:
            self._enter_state('ABORT')
            self.channel.send_to(self.coordinator, VOTE_ABORT)
            return "Participant {} terminated in state ABORT due to LOCAL_ABORT.".format(
                self.participant
            )

        # vote commit
        self._enter_state('READY')
        self.channel.send_to(self.coordinator, VOTE_COMMIT)

        # Phase 2b: wait for PREPARE_COMMIT or GLOBAL_ABORT
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        if not msg:
            self._terminate_after_coordinator_crash()
            return "Participant {} terminated in state {} due to coordinator crash (P_k={}).".format(
                self.participant, self.state, self._new_coordinator_id()
            )

        if msg[1] == GLOBAL_ABORT:
            self._enter_state('ABORT')
            return "Participant {} terminated in state ABORT due to GLOBAL_ABORT.".format(
                self.participant
            )

        assert msg[1] == PREPARE_COMMIT
        self._enter_state('PRECOMMIT')
        self.channel.send_to(self.coordinator, READY_COMMIT)

        # Phase 3b: wait for GLOBAL_COMMIT
        msg = self.channel.receive_from(self.coordinator, TIMEOUT)
        if not msg:
            self._terminate_after_coordinator_crash()
            return "Participant {} terminated in state {} due to coordinator crash (P_k={}).".format(
                self.participant, self.state, self._new_coordinator_id()
            )

        if msg[1] == GLOBAL_COMMIT:
            self._enter_state('COMMIT')
            return "Participant {} terminated in state COMMIT due to GLOBAL_COMMIT.".format(
                self.participant
            )

        # Any other message => abort (minimal, no recovery/termination logic)
        self._enter_state('ABORT')
        return "Participant {} terminated in state ABORT due to unexpected message {}.".format(
            self.participant, msg[1]
        )

