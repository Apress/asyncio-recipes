import asyncio
import os

pid_loops = {}


def get_event_loop():
    pid = os.getpid()
    if pid not in pid_loops:
        pid_loops[pid] = asyncio.new_event_loop()
    return pid_loops[pid]


def asyncio_init():
    pid = os.getpid()
    pid_loops[pid] = asyncio.new_event_loop()
    pid_loops[pid].pid = pid


os.register_at_fork(after_in_parent=asyncio_init, after_in_child=asyncio_init)

if os.fork() == 0:
    # Child
    loop = get_event_loop()
    assert os.getpid() == loop.pid
else:
    # Parent
    loop = get_event_loop()
    assert os.getpid() == loop.pid
