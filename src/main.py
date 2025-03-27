import logging
import os
import sys
import time
from typing import NoReturn

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


def pxc_start(args: list[str]) -> NoReturn:
    lldb_host = LLDBHost(sys.executable, args)

    while True:
        time.sleep(0.25) # FIXME: sleep is required for I/O purposes, but this should be done asynchronously
        stdout = lldb_host.get_stdout()
        if stdout:
            if stdout.endswith("(Pdb) "):
                print(stdout[:-6])
            else:
                print(stdout)
        stderr = lldb_host.get_stderr()
        if stderr:
            print(stderr, file=sys.stderr)

        if lldb_host.is_stopped():
            output, result = lldb_host.execute("process status")
            if output:
                file = sys.stderr if not result else sys.stdout
                print(output, file=file)

        command = input("(pxc-dbg) > ")
        if command.startswith("py "):
            actual_command = command[3:]
            logger.debug(f"Sending command to child: {actual_command}")
            lldb_host.set_stdin(actual_command + "\n")

        elif command.startswith("c "):
            actual_command = command[2:]
            output, result = lldb_host.execute(actual_command)
            if output:
                file = sys.stderr if not result else sys.stdout
                print(output, file=file)

        elif command == "exit" or command == "quit" or command == "q":
            lldb_host.stop_events_handler()
            exit(0)

        elif command == "":
            pass

        else:
            print("Unknown Command", file=sys.stderr)


def main() -> NoReturn:
    if len(sys.argv) <= 1:  # ???: Might need to update to work as a module
        print("Expected at least one argument", file=sys.stderr)
        exit(1)

    pxc_start(["-m", "pdb"] + sys.argv[1:])


if __name__ == "__main__":
    main()
