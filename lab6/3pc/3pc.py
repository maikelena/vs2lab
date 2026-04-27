"""
Application performing a distributed commit using 3PC
- sets up a group of participants and one coordinator
- nodes run in separate processes (works on unix and windows)
"""

import multiprocessing as mp
import logging

import coordinator
import participant
from context import lab_channel, lab_logging

lab_logging.setup(stream_level=logging.INFO, file_level=logging.DEBUG)

logger = logging.getLogger("vs2lab.lab6.3pc.3pc")


def create_and_run(num_bits, proc_class, enter_bar, run_bar):
    chan = lab_channel.Channel(n_bits=num_bits)
    proc = proc_class(chan)
    enter_bar.wait()
    proc.init()
    run_bar.wait()
    logger.info(proc.run())


if __name__ == "__main__":
    m = 8  # Number of bits for process ids
    n = 3  # Number of participants in the group

    # Flush communication channel
    chan = lab_channel.Channel()
    chan.channel.flushall()

    # we need to spawn processes for support of windows
    mp.set_start_method('spawn')

    # create barriers to synchronize bootstrapping
    bar1 = mp.Barrier(n + 1)
    bar2 = mp.Barrier(n + 1)

    # start n participants in separate processes
    participants = []
    for i in range(n):
        participant_proc = mp.Process(
            target=create_and_run,
            name="Participant-" + str(i),
            args=(m, participant.Participant, bar1, bar2))
        participants.append(participant_proc)
        participant_proc.start()

    # start coordinator in separate process
    coordinator_proc = mp.Process(
        target=create_and_run,
        name="Coordinator",
        args=(m, coordinator.Coordinator, bar1, bar2))
    coordinator_proc.start()

    coordinator_proc.join()
    for participant_proc in participants:
        participant_proc.join()

