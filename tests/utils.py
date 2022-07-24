import asyncio
import socket
import time
from typing import Iterable


def is_connectable(host, port):
    sock = None
    try:
        sock = socket.create_connection((host, port), timeout=1)
    except socket.error:
        return False
    else:
        return True
    finally:
        if sock is not None:
            sock.close()


def wait_until_connectable(host, port, timeout=10):
    count = 0
    while not is_connectable(host=host, port=port):
        if count >= timeout:
            raise Exception(
                f'The proxy server has not available by ({host}, {port}) in {timeout:d} seconds'
            )
        count += 1
        time.sleep(1)
    return True


def cancel_tasks(tasks: Iterable[asyncio.Task], loop: asyncio.AbstractEventLoop):
    if not tasks:
        return

    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during asyncio.run() shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )


def cancel_all_tasks(loop: asyncio.AbstractEventLoop):
    tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
    cancel_tasks(tasks=tasks, loop=loop)
