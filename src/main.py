import sys
import logging
import os
import time
from typing import NoReturn
import threading
import pickle
import socket

from LLDBHost import LLDBHost
from pxc import PXC
from IOManager import IOManager


HOST = "127.0.0.1"
PORT = 30_000
pipe = ...

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


HELP_TEXT = """\
    (h)elp: print this help text
    (b)reak or breakpoint <symbol name>: sets breakpoint in both C/C++ and Python
    (n)ext: steps over current line of code
    (s)tep: steps into the function
    (c)ontinue: continue execution until next breakpoint is reached
    (v)ars: print all local variables
    (bt)backtrace: print backtrace
    (p)rint <variable>: prints the value of the variable
    (pp)rint <variable>: pretty prints the value of the variable
    pdb <command ...>: sends command to pdb session
    lldb <command ...>: sends command to lldb session
    exit or quit: exits debugger
"""

pxc = ...


def pxc_start(args: list[str]) -> NoReturn:
    global pxc, pipe
    io_manager = IOManager("(px-dbg) > ")
    io_manager.start()
    lldb_host = LLDBHost(sys.executable, io_manager, args)
    pxc = PXC(lldb_host, io_manager)

    while True:
        command = io_manager.read()
        while command is None:
            time.sleep(0)
            command = io_manager.read()

        if pipe != Ellipsis:
            pipe.send(pickle.dumps(False))

        if command.startswith("pdb "):
            actual_command = command[4:]
            logger.debug(f"Sending command to pdb: {actual_command}")
            lldb_host.set_stdin(actual_command + "\n")

        elif command.startswith("lldb "):
            actual_command = command[5:]
            output, _ = lldb_host.execute(actual_command)
            if output:
                io_manager.write(output)

        # handle help
        elif command == "h" or command == "help":
            io_manager.write(HELP_TEXT)

        # handle printing locals
        elif command == "v" or command == "vars":
            pxc.print_variables()

        # handle backtrace
        elif command == "bt" or command == "backtrace":
            pxc.print_backtrace()

        # handle breakpoints
        elif command.startswith("b "):
            pxc.set_breakpoint(command[2:].strip())
        elif command.startswith("break "):
            pxc.set_breakpoint(command[6:].strip())
        elif command.startswith("breakpoint "):
            pxc.set_breakpoint(command[11:].strip())
        # handle breakpoint actions
        elif command.startswith("br "):
            pxc.process_breakpoints(command[3:].strip())
        elif command.startswith("breakpoints "):
            pxc.process_breakpoints(command[12:].strip())

        # handle step over
        elif command == "n" or command == "next":
            pxc.step_over()

        # handle step in
        elif command == "s" or command == "step":
            if pipe != Ellipsis:
                pipe.send(
                    pickle.dumps(True)
                )  # ???: should be done after checking lldb_host.is_stopped()
            pxc.step_in()

        # handle continue
        elif command == "c" or command == "continue":
            pxc.continue_execution()

        # handle print
        elif command.startswith("p "):
            pxc.print_variable(command[2:].strip())
        elif command.startswith("print "):
            pxc.print_variable(command[6:].strip())

        # handle pretty print
        elif command.startswith("pp "):
            pxc.pprint_variable(command[3:].strip())
        elif command.startswith("pprint "):
            pxc.pprint_variable(command[7:].strip())

        elif command == "exit" or command == "quit":
            if pipe != Ellipsis:
                pipe.send(pickle.dumps(None))
            lldb_host.set_stdin("exit" + "\n")
            lldb_host.stop()
            io_manager.stop()
            break

        elif command == "":
            io_manager.write("")

        else:
            io_manager.write("Unknown Command")

        pxc.process_python_command_queue()


def connect_debugee():
    global pipe
    with socket.socket() as s:
        while True:
            try:
                s.connect((HOST, PORT))
            except ConnectionRefusedError as e:
                time.sleep(0)
            else:
                logger.debug(f"Connection to debugee successful")
                break
        pipe = s
        while True:
            try:
                data = s.recv(1024 * 4)
                if not data:
                    break
                data = pickle.loads(data)
                logger.debug(f"Data received from debugee server: {data}")
                fn_loc = data[-1] + 16 + 8
                logger.debug(f"Setting a break point at {fn_loc}")
                pxc.lldb_host.execute(f"b *{hex(fn_loc)}")

            except ConnectionResetError:
                break


def main() -> NoReturn:
    if len(sys.argv) <= 1:  # ???: Might need to update to work as a module
        print("Expected at least one argument", file=sys.stderr)
        exit(1)

    debugee_server = threading.Thread(target=connect_debugee)
    logger.debug(f"Starting connection to debugee")
    debugee_server.start()

    from pathlib import Path

    dir_loc = Path(__file__).parent
    pxc_module_path = dir_loc / "pxcdb.py"
    pxc_start([str(pxc_module_path), *sys.argv[1:]])

    debugee_server.join()
    logger.debug("Exiting safely")


if __name__ == "__main__":
    main()
