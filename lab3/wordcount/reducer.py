import sys

import zmq

import constWC


def _parse_id(argv: list[str]) -> int:
    if len(argv) >= 2:
        return int(argv[1])
    return 0


def main() -> int:
    reducer_id = _parse_id(sys.argv)
    if reducer_id not in (0, 1):
        raise ValueError("reducer_id must be 0 or 1")

    context = zmq.Context()
    pull = context.socket(zmq.PULL)
    pull.bind(constWC.reducer_bind_addr(reducer_id))

    counts: dict[str, int] = {}
    end_seen = 0

    while True:
        msg = pull.recv()
        if msg == constWC.END_TOKEN:
            end_seen += 1
            if end_seen >= constWC.NUM_MAPPERS:
                break
            continue

        word = msg.decode("utf-8").strip()
        if not word:
            continue
        counts[word] = counts.get(word, 0) + 1
        print(f"{word} {counts[word]}", flush=True)

    pull.close(linger=0)
    context.term()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

