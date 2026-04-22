import os

# Minimal constants for Lab3 wordcount pipeline.
#
# Bind on "*" for container friendliness; clients connect via HOST.

END_TOKEN = b"__END__"

NUM_MAPPERS = 3

HOST = os.environ.get("WC_HOST", "127.0.0.1")

# Splitter PUSHes sentences to mappers (mappers PULL).
SPLITTER_PORT = os.environ.get("WC_SPLITTER_PORT", "5557")

# Reducers PULL words from mappers (mappers PUSH).
REDUCER0_PORT = os.environ.get("WC_REDUCER0_PORT", "5558")
REDUCER1_PORT = os.environ.get("WC_REDUCER1_PORT", "5559")


def splitter_bind_addr() -> str:
    return f"tcp://*:{SPLITTER_PORT}"


def splitter_connect_addr() -> str:
    return f"tcp://{HOST}:{SPLITTER_PORT}"


def reducer_bind_addr(reducer_id: int) -> str:
    if reducer_id == 0:
        return f"tcp://*:{REDUCER0_PORT}"
    if reducer_id == 1:
        return f"tcp://*:{REDUCER1_PORT}"
    raise ValueError("reducer_id must be 0 or 1")


def reducer_connect_addr(reducer_id: int) -> str:
    if reducer_id == 0:
        return f"tcp://{HOST}:{REDUCER0_PORT}"
    if reducer_id == 1:
        return f"tcp://{HOST}:{REDUCER1_PORT}"
    raise ValueError("reducer_id must be 0 or 1")

