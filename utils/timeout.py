# Copyright (C) 2015-2016 Skylable Ltd. <info-copyright@skylable.com>
# License: MIT, see LICENSE for more details.

from contextlib import contextmanager
import signal


class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds=9, error_message="Operation timed out."):
    def handle_timeout(signum, frame):
        raise TimeoutError(error_message)

    signal.signal(signal.SIGALRM, handle_timeout)
    signal.alarm(seconds)
    yield
    signal.alarm(0)
