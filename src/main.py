import logging
import os
import sys
import pty
from typing import NoReturn
from pdb import __file__ as pdb_file

from utils import readfd
from LLDBHost import LLDBHost


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


def master(pid: int, fd: int) -> NoReturn:
    os.set_blocking(fd, False)

    lldb_host = LLDBHost(pid)

    while True:
        result = readfd(fd)
        if result:
            if result.endswith("(Pdb) "):
                print(result[:-6])
            else:
                print(result)

        command = input("(pxc-dbg) > ")
        if command.startswith("py "):
            actual_command = command[3:]
            logger.debug(f"Sending command to child: {actual_command}")
            os.write(fd, (actual_command + "\n").encode())

        elif command.startswith("c "):
            actual_command = command[2:]
            output, result = lldb_host.execute(actual_command)
            if output:
                file = sys.stderr if not result else sys.stdout
                print(output, file=file)

        elif command == "exit" or command == "quit" or command == "q":
            os.write(fd, "exit\n".encode())
            lldb_host.stop_events_handler()
            exit(0)

        elif command == "":
            pass

        else:
            print("Unknown Command", file=sys.stderr)


def child(args: list[str]) -> NoReturn:
    args = ["-m", pdb_file] + args
    logger.debug(f"Executing child process: {sys.executable} {args}")
    os.execvp(sys.executable, args)


def main() -> NoReturn:
    if len(sys.argv) <= 1:  # ???: Might need to update to work as a module
        print("Expected at least one argument", file=sys.stderr)
        exit(1)

    logger.debug("Forking")
    pid, fd = pty.fork()
    if pid == 0:
        logger.debug(f"Child process starting: {os.getpid()}")
        child(sys.argv[1:])
    else:
        logger.debug(f"Parent process starting: {os.getpid()} child is {pid}")
        master(pid, fd)


if __name__ == "__main__":
    main()
