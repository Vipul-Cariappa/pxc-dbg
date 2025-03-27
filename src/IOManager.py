import os
import sys
from typing import Optional
from threading import Lock

import logging

logger = logging.getLogger("pxc-dbg")

io_lock = Lock()


class IOManager:
    def __init__(self, prompt: str = ">>> "):
        self.prompt = prompt
        self.backspace = "\b" * len(prompt)
        self.replace_blank = self.backspace + " " * (len(prompt) - 1)

    def start(self):
        with io_lock:
            print(self.prompt, end="", flush=True)

    def stop(self):
        with io_lock:
            print(self.replace_blank, end="", flush=True)

    def write(self, data: str, prompt: bool = True):
        with io_lock:
            logger.debug(f"Write: {data}")
            print(
                self.replace_blank,
                self.backspace,
                data[:-6] if data.endswith("(Pdb) ") else data,
                "\n",
                self.prompt if prompt else "",
                end="",
                flush=True,
            )

    def read(self, blocking: bool = False) -> Optional[str]:
        with io_lock:
            os.set_blocking(sys.stdin.fileno(), blocking)
            try:
                content = os.read(sys.stdin.fileno(), 1024 * 1024 * 10).decode().strip()
            except BlockingIOError:
                content = None

        if content is not None:
            logger.debug(f"Read: {content}")
        return content


if __name__ == "__main__":
    # testing IOManager here
    io = IOManager()
    io.start()
    io.write("Hello World")
    io.write("Got: " + io.read(True))
    io.stop()
