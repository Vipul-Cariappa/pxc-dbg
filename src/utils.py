import os
import time
from typing import Optional, Any
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from LLDBHost import LLDBHost


def readfd(fd: int, blocking: bool = False) -> Optional[str]:
    time.sleep(
        0.1
    )  # FIXME: to be safe this is needed, but we should do this asynchronously
    block = True
    while block:
        try:
            data = os.read(fd, 1024 * 1024 * 10)  # read 10MBs at a time
            if data:
                string = data.decode("utf-8")
                return string
        except BlockingIOError:
            block = blocking
            if block:
                time.sleep(0.1)


class Terminate:
    pass


class LLDBProcessWrapper:
    @staticmethod
    def run(pid: int, pipe: Connection):
        instance = LLDBHost(pid)
        while True:
            command = pipe.recv()
            if isinstance(command, Terminate):
                instance.stop_events_handler()
                exit(0)
            output, result = instance.execute(command)
            pipe.send((output, result))


def CreateLLDBProcess(pid: int) -> Connection:
    parent_conn, child_conn = Pipe()
    p = Process(target=LLDBProcessWrapper.run, args=(pid, child_conn))
    p.start()
    return parent_conn
