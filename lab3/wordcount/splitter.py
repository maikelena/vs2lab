import random
import time

import zmq

import constWC

SENTENCE_POOL = [
    "Today is a great day",
    "You are doing really well",
    "Keep going you can do it",
    "Learning distributed systems is fun",
    "Small steps lead to big progress",
    "Everything will work out",
    "Be kind and stay positive",
    "Practice makes progress",
    "This lab will be finished soon",
    "Good things take time",
    "You can solve hard problems",
    "Focus and breathe you got this",
    "Teamwork makes things easier",
    "A calm mind helps you learn",
    "Success is built on consistency",
    "Your effort will pay off",
    "You are closer than you think",
    "It is okay to make mistakes",
    "Every run teaches you something",
    "Great work keep it up",
]

def main() -> int:
    context = zmq.Context()
    push = context.socket(zmq.PUSH)
    push.bind(constWC.splitter_bind_addr())

    # Give mappers a moment to connect.
    time.sleep(1)

    for _ in range(80):
        sentence = random.choice(SENTENCE_POOL)
        push.send_string(sentence)

    # Send exactly one END per mapper to ensure each mapper receives a stop signal.
    for _ in range(constWC.NUM_MAPPERS):
        push.send(constWC.END_TOKEN)

    push.close(linger=0)
    context.term()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

