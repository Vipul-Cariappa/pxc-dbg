import os
import logging
import lldb
from threading import Thread

logger = logging.getLogger("pxc-dbg")


class LLDBException(Exception):
    pass


class LLDBEventHandler(Thread):
    def __init__(self, debugger: "LLDBHost"):
        super().__init__()
        self.debugger_host = debugger
        self.stop_event_handler = False

    def run(self):
        listener = self.debugger_host.debugger.GetListener()
        event = lldb.SBEvent()
        while not self.stop_event_handler:
            if listener.WaitForEvent(1, event):
                stream = lldb.SBStream()
                event.GetDescription(stream)
                logger.debug(f"Received LLDB Event: {stream.GetData()}")
        listener.Clear()


class LLDBHost:
    def __init__(self, exe: str, args: list[str] = []):
        logger.debug("Creating lldb instance")
        self.exe = exe
        self.args = args
        self.debugger = lldb.SBDebugger.Create()
        self.debugger.SetAsync(True)
        self.debugger.SetUseColor(True)

        self.command_interpreter = self.debugger.GetCommandInterpreter()

        logger.debug(f"Creating target for {self.exe}")
        self.target = self.debugger.CreateTarget(self.exe)

        logger.debug(f"Launching process for {self.exe} with args {self.args}")
        self.process = self.target.LaunchSimple(self.args, None, os.getcwd())

        self.start_events_handler()

    def get_stdout(self) -> str:
        return self.process.GetSTDOUT(1024 * 1024 * 10)

    def get_stderr(self) -> str:
        return self.process.GetSTDERR(1024 * 1024 * 10)

    def set_stdin(self, data: str) -> None:
        self.process.PutSTDIN(data)

    def is_stopped(self) -> bool:
        return self.process.GetState() == lldb.eStateStopped

    def start_events_handler(self):
        self.events_handler = LLDBEventHandler(self)
        self.events_handler.start()

    def stop_events_handler(self):
        self.events_handler.stop_event_handler = True
        self.events_handler.join()

    def execute(self, command: str) -> tuple[str, bool]:
        """
        Executes the given command.
        Returns a tuple of the output and a boolean indicating whether the command succeeded.
        """

        result = lldb.SBCommandReturnObject()
        logger.debug(f"Executing lldb command: {command}")
        self.command_interpreter.HandleCommand(command, result)

        if result.Succeeded():
            result_string = result.GetOutput()
            logger.debug(f"Lldb result success: {result_string}")
            return (result_string, True)

        result_string = result.GetError()
        logger.debug(f"Lldb result failure: {result_string}")
        return (result_string, False)
