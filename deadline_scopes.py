import time
import socket
import threading
from contextlib import contextmanager
from functools import wraps

import attr

__all__ = [
    "open_deadline_scope", "check_timeout", "Cancelled",
    "move_on_after", "fail_after", "TooSlowError",
    "DeadlineSocket", "deadline_socket", "DeadlineLock",
]


_stack_holder = threading.local()


def _scope_stack():
    return getattr(_stack_holder, "value", [])


def _now():
    return time.monotonic()


@attr.s
class DeadlineScope:
    deadline = attr.ib(default=float("inf"))
    caught = attr.ib(default=None)


@attr.s
class Cancelled(BaseException):
    _scope = attr.ib()


def check_timeout(default=float("inf")):
    """If some timeout has expired, raise an appropriate exception. If no
    timeouts are in effect, return ``default``. Otherwise, return the current
    effective timeout."""
    now = _now()
    stack = _scope_stack()
    # Find the outermost expired scope (if any)
    for ds in _scope_stack():
        if ds.deadline <= now:
            raise Cancelled(ds)
    # Handle default
    if not stack:
        return default
    # Find the effective timeout
    return min(ds.deadline for ds in stack) - now


@contextmanager
def open_deadline_scope(when):
    ds = DeadlineScope(when)
    _scope_stack().append(ds)
    try:
        yield ds
    except Cancelled as exc:
        if exc._scope is ds:
            ds.caught = exc
        else:
            raise
    finally:
        popped = _scope_stack().pop()
        assert popped is ds


@contextmanager
def move_on_after(seconds):
    with open_deadline_scope(now() + seconds) as ds:
        yield ds


@contextmanager
def fail_after(seconds):
    with move_on_after(seconds) as ds:
        yield
    if ds.caught is not None:
        raise TooSlowError from ds.caught


_BLOCKING_SOCKET_METHODS = {
    "accept", "bind", "close", "connect", "connect_ex", "recv", "recvfrom",
    "recvmsg", "recvmsg_into", "recvfrom_into", "recv_into", "send",
    "sendall", "sendto", "sendmsg", "sendmsg_afalg", "sendfile",
}


@attr.s
class DeadlineSocket:
    """Like socket.socket, but deadline-scope aware."""
    wrapped = attr.ib()

    def _blocking_method(self, meth):
        @wraps(meth)
        def wrapped_method(*args, **kwargs):
            self.settimeout(check_timeout(None))
            try:
                return meth(*args, **kwargs)
            except socket.timeout:
                check_timeout()  # should raise
                assert False

    def __getattr__(self, name):
        if name in _BLOCKING_SOCKET_METHODS:
            return self._blocking_method(getattr(self.wrapped, name))
        else:
            return getattr(self.wrapped, name)

    def __dir__(self):
        return self.wrapped.__dir__()


# Convenience constructor
def deadline_socket(*args, **kwargs):
    return DeadlineSocket(socket.socket(*args, **kwargs))


@attr.s
class DeadlineLock:
    """Like threading.Lock, but deadline-scope aware."""
    wrapped = attr.ib(default=attr.Factory(threading.Lock))

    def acquire(self, blocking=True):
        if blocking:
            if self.wrapped.acquire(timeout=check_timeout(-1)):
                return True
            else:
                check_timeout()  # should raise
                assert False
        else:
            return self.wrapped.acquire(blocking=False)

    def release(self):
        self.wrapped.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, *args):
        self.release()
