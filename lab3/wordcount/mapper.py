import re
import sys
import time

import zmq

import constWC


_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _partition(word: str) -> int:
    # Simple deterministic partition: same word length => same reducer.
    return len(word) % 2

def _normalize_and_split(sentence: str) -> list[str]:
    return _TOKEN_RE.findall(sentence.lower())


def main() -> int:
    context = zmq.Context()

    mapper_id = sys.argv[1] if len(sys.argv) > 1 else "?"
    print(f"mapper {mapper_id} started", flush=True)

    pull = context.socket(zmq.PULL)
    pull.connect(constWC.splitter_connect_addr())

    push_r0 = context.socket(zmq.PUSH)
    push_r0.connect(constWC.reducer_connect_addr(0))

    push_r1 = context.socket(zmq.PUSH)
    push_r1.connect(constWC.reducer_connect_addr(1))

    reducers = (push_r0, push_r1)

    # Allow connections to settle.
    time.sleep(0.2)

    while True:
        msg = pull.recv()
        if msg == constWC.END_TOKEN:
            # Signal both reducers that this mapper is done.
            push_r0.send(constWC.END_TOKEN)
            push_r1.send(constWC.END_TOKEN)
            break

        sentence = msg.decode("utf-8")
        for word in _normalize_and_split(sentence):
            r = _partition(word)
            reducers[r].send_string(word)

    pull.close(linger=0)
    push_r0.close(linger=0)
    push_r1.close(linger=0)
    context.term()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

