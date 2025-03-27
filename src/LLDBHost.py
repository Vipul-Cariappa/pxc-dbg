import logging
import lldb
from threading import Thread

logger = logging.getLogger("pxc-dbg")


class LLDBException(Exception):
    pass


class LLDBEventHandler(Thread):
    def __init__(self, debugger: lldb.SBDebugger):
        super().__init__()
        self.debugger = debugger
        self.stop_event_handler = False

    def run(self):
        listener = self.debugger.GetListener()
        event = lldb.SBEvent()
        while not self.stop_event_handler:
            if listener.WaitForEvent(1, event):
                stream = lldb.SBStream()
                event.GetDescription(stream)
                logger.debug(f"Received LLDB Event: {stream.GetData()}")
        listener.Clear()


class LLDBHost:
    def __init__(self, pid: int):
        logger.debug("Creating lldb instance")
        self.pid = pid
        self.debugger = lldb.SBDebugger.Create()
        self.debugger.SetAsync(True)
        self.debugger.SetUseColor(True)

        self.command_interpreter = self.debugger.GetCommandInterpreter()

        logger.debug(f"Attaching to {pid}")
        output, result = self.execute(f"attach -p {pid}")
        if not result:
            raise LLDBException(f"Failed to attach to {pid}:\n{output}")

        # continue execution. attaching stops execution
        output, result = self.execute(f"c")
        if not result:
            raise LLDBException(f"Failed to continue{pid}:\n{output}")

        self.start_events_handler()

    def start_events_handler(self):
        self.events_handler = LLDBEventHandler(self.debugger)
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
