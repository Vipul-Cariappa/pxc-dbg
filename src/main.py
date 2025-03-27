import logging
import os
import sys
import time
from typing import NoReturn

from LLDBHost import LLDBHost
from IOManager import IOManager


# Setup logging
logger = logging.getLogger("pyc-dbg")
log_level = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}[os.getenv("LOG_LEVEL", "CRITICAL")]
log_file = os.getenv("LOG_FILE", None)
if log_file:
    logging.basicConfig(level=log_level, filename=log_file)
else:
    logging.basicConfig(level=log_level)


def pxc_start(args: list[str]) -> NoReturn:
    io_manager = IOManager("(px-dbg) > ")
    io_manager.start()
    lldb_host = LLDBHost(sys.executable, io_manager, args)

    while True:
        command = io_manager.read()
        while command is None:
            time.sleep(0.25)
            command = io_manager.read()

        if command.startswith("py "):
            actual_command = command[3:]
            logger.debug(f"Sending command to pdb: {actual_command}")
            lldb_host.set_stdin(actual_command + "\n")

        elif command.startswith("c "):
            actual_command = command[2:]
            output, _ = lldb_host.execute(actual_command)
            if output:
                io_manager.write(output)

        elif command == "exit" or command == "quit" or command == "q":
            lldb_host.stop_events_handler()
            io_manager.stop()
            exit(0)

        elif command == "":
            io_manager.write("")

        else:
            io_manager.write("Unknown Command")


def main() -> NoReturn:
    if len(sys.argv) <= 1:  # ???: Might need to update to work as a module
        print("Expected at least one argument", file=sys.stderr)
        exit(1)

    pxc_start(["-m", "pdb"] + sys.argv[1:])


if __name__ == "__main__":
    main()
