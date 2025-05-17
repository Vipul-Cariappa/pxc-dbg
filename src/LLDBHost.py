import os
import logging
import lldb
from IOManager import IOManager
from threading import Thread

logger = logging.getLogger("pxc-dbg")


class LLDBException(Exception):
    pass


class LLDBEventHandler(Thread):
    def __init__(self, debugger: "LLDBHost", io_manager: IOManager):
        super().__init__()
        self.debugger_host = debugger
        self.stop_event_handler = False
        self.io_manager = io_manager

    def run(self):
        listener = self.debugger_host.debugger.GetListener()
        event = lldb.SBEvent()
        while not self.stop_event_handler:
            if listener.WaitForEvent(1, event):
                if event.GetBroadcaster().GetName() == "lldb.process":
                    if (
                        event.GetType() == lldb.SBProcess.eBroadcastBitStateChanged
                        and self.debugger_host.is_stopped()
                    ):
                        output, result = self.debugger_host.execute("process status")
                        assert result
                        if output:
                            self.io_manager.write(output)
                    elif event.GetType() == lldb.SBProcess.eBroadcastBitSTDOUT:
                        output = self.debugger_host.get_stdout()
                        if output:
                            self.io_manager.write(output)
                    elif event.GetType() == lldb.SBProcess.eBroadcastBitSTDERR:
                        output = self.debugger_host.get_stderr()
                        if output:
                            self.io_manager.write(output)

                stream = lldb.SBStream()
                event.GetDescription(stream)
                logger.debug(f"Received LLDB Event: {stream.GetData()}")

        listener.Clear()


class LLDBHost:
    def __init__(self, exe: str, io_manager: IOManager, args: list[str] = []):
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

        self.start_events_handler(io_manager)

    def get_stdout(self) -> str:
        logger.debug("Getting STDOUT")
        return self.process.GetSTDOUT(1024 * 1024 * 10)

    def get_stderr(self) -> str:
        logger.debug("Getting STDERR")
        return self.process.GetSTDERR(1024 * 1024 * 10)

    def set_stdin(self, data: str) -> None:
        logger.debug(f"Putting {data} to STDIN")
        self.process.PutSTDIN(data)

    def is_stopped(self) -> bool:
        return self.process.GetState() == lldb.eStateStopped

    def start_events_handler(self, io_manager: IOManager):
        self.events_handler = LLDBEventHandler(self, io_manager)
        self.events_handler.start()

    def stop_events_handler(self):
        self.events_handler.stop_event_handler = True
        self.events_handler.join()

    def stop(self):
        self.stop_events_handler()
        self.process.Destroy()

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
