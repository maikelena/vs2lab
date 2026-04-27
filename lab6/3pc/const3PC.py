
# coordinator messages
VOTE_REQUEST = 'VOTE_REQUEST'
PREPARE_COMMIT = 'PREPARE_COMMIT'
GLOBAL_COMMIT = 'GLOBAL_COMMIT'
GLOBAL_ABORT = 'GLOBAL_ABORT'

# participant messages
VOTE_COMMIT = 'VOTE_COMMIT'
VOTE_ABORT = 'VOTE_ABORT'
READY_COMMIT = 'READY_COMMIT'

# participant decisions
LOCAL_ABORT = 'LOCAL_ABORT'
LOCAL_SUCCESS = 'LOCAL_SUCCESS'

# fail-noisy crash timeout (no termination protocol in minimal version)
TIMEOUT = 1

