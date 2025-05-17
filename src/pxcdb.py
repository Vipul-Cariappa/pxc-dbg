import sys
import os
import logging
from pdb import Pdb, _usage, _ModuleTarget, _ScriptTarget, Restart
import traceback
import socket
import threading
import pickle
import time


HOST = "127.0.0.1"
PORT = 30_000
pipe = ...
intercept_c_call = False


# Setup logging
logger = logging.getLogger("pyc-debugee")
log_level = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}[os.getenv("LOG_LEVEL", "CRITICAL")]
log_file = os.getenv("LOG_FILE_DEBUGEE", None)
if log_file:
    logging.basicConfig(level=log_level, filename=log_file)
else:
    logging.basicConfig(level=log_level)


class PSXDB(Pdb):
    def __init__(
        self,
        completekey="tab",
        stdin=None,
        stdout=None,
        skip=None,
        nosigint=False,
        readrc=True,
    ):
        super().__init__(completekey, stdin, stdout, skip, nosigint, readrc)
        sys.setprofile(self.cfunction_dispatch_handler)

    def cfunction_dispatch_handler(self, frame, event, arg):
        if pipe == Ellipsis:
            return self.cfunction_dispatch_handler

        if event == "c_call" and intercept_c_call:
            logger.debug("Sending c_call")
            pipe.send(pickle.dumps(("c_call", arg.__name__, id(arg))))
            # TODO: A C helper function is required here doing what
            #       CPython's cfunction_call function does but it should
            #       return the function pointer instead.
            #       Along with the arg.__name__ this might be able to
            #       search the appropriate address when overloads like
            #       __add__ or __getitem__ need to be stepped into
            time.sleep(
                1
            )  # TODO: wait till you receive something from the controller process
        elif event == "c_return" and intercept_c_call:
            logger.debug("Sending c_return")
            pipe.send(pickle.dumps(("c_return", arg.__name__, id(arg))))
        elif event == "c_exception" and intercept_c_call:
            logger.debug("Sending c_exception")
            pipe.send(pickle.dumps(("c_exception", arg.__name__, id(arg))))

        return self.cfunction_dispatch_handler


def start_debugger():
    import getopt

    opts, args = getopt.getopt(sys.argv[1:], "mhc:", ["help", "command="])

    if not args:
        print(_usage)
        sys.exit(2)

    if any(opt in ["-h", "--help"] for opt, optarg in opts):
        print(_usage)
        sys.exit()

    commands = [optarg for opt, optarg in opts if opt in ["-c", "--command"]]

    module_indicated = any(opt in ["-m"] for opt, optarg in opts)
    cls = _ModuleTarget if module_indicated else _ScriptTarget
    target = cls(args[0])

    target.check()

    sys.argv[:] = args  # Hide "pdb.py" and pdb options from argument list

    # Note on saving/restoring sys.argv: it's a good idea when sys.argv was
    # modified by the script being debugged. It's a bad idea when it was
    # changed by the user from the command line. There is a "restart" command
    # which allows explicit specification of command line arguments.
    pdb = PSXDB()
    pdb.rcLines.extend(commands)
    while True:
        try:
            pdb._run(target)
            if pdb._user_requested_quit:
                break
            print("The program finished and will be restarted")
        except Restart:
            print("Restarting", target, "with arguments:")
            print("\t" + " ".join(sys.argv[1:]))
        except SystemExit as e:
            # In most cases SystemExit does not warrant a post-mortem session.
            print("The program exited via sys.exit(). Exit status:", end=" ")
            print(e)
        except SyntaxError:
            traceback.print_exc()
            sys.exit(1)
        except BaseException as e:
            traceback.print_exc()
            print("Uncaught exception. Entering post mortem debugging")
            print("Running 'cont' or 'step' will restart the program")
            t = e.__traceback__
            pdb.interaction(None, t)
            print("Post mortem debugger finished. The " + target + " will be restarted")


def start_debugger_server():
    # TODO: don't listen here, thereby eliminating the use of threads
    global intercept_c_call, pipe
    with socket.socket() as s:
        logging.debug("Starting socket")
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        logger.debug(f"Connected to {addr}")
        with conn:
            pipe = conn
            while True:
                data = conn.recv(1024 * 4)
                if not data:
                    time.sleep(0)
                    continue
                intercept_c_call = pickle.loads(data)
                logger.debug(f"Received: {intercept_c_call}")
                if intercept_c_call is None:
                    break
        pipe = None
    logger.debug("Ending")


def main():
    debugger_server = threading.Thread(target=start_debugger_server)
    logger.debug("Starting thread")
    debugger_server.start()

    start_debugger()
    debugger_server.join()
    logger.debug("Exiting safely")


# When invoked as main program, invoke the debugger on a script
if __name__ == "__main__":
    import pxcdb

    pxcdb.main()
