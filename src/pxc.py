import lldb
from typing import Optional
from LLDBHost import LLDBHost
from IOManager import IOManager


class PXC:
    def __init__(self, lldb_host: LLDBHost, io_manager: IOManager):
        self.lldb_host = lldb_host
        self.io_manager = io_manager

        # commands to execute in pdb once process continues
        # i.e. process is in stop state when things are enqueued
        self.python_command_queue: list[str] = []

    def set_breakpoint(self, symbol: str) -> None:
        # lldb
        output, _ = self.lldb_host.execute(f"b {symbol}")

        # python
        if not self.lldb_host.is_stopped():
            self.lldb_host.set_stdin(f"b {symbol}\n")
        else:
            self.python_command_queue.append(f"break {symbol}")

        self.io_manager.write(output)

    def process_breakpoints(self, action: str) -> None:
        raise NotImplementedError

    def step_over(self) -> None:
        if self.lldb_host.is_stopped():
            output, _ = self.lldb_host.execute("n")
            self.io_manager.write(output)
        else:
            self.lldb_host.set_stdin("n\n")

    def step_in(self) -> None:
        # TODO: cross step-in
        if self.lldb_host.is_stopped():
            output, _ = self.lldb_host.execute("s")
            self.io_manager.write(output)
        else:
            self.lldb_host.set_stdin("s\n")

    def continue_execution(self) -> None:
        if self.lldb_host.is_stopped():
            output, _ = self.lldb_host.execute("c")
            self.io_manager.write(output)
        else:
            self.lldb_host.set_stdin("c\n")

    def print_variable(self, variable: str) -> None:
        if self.lldb_host.is_stopped():
            output, _ = self.lldb_host.execute(f"p {variable}")
            self.io_manager.write(output)
        else:
            self.lldb_host.set_stdin(f"p {variable}\n")

    def pprint_variable(self, variable: str) -> None:
        if self.lldb_host.is_stopped():
            output, _ = self.lldb_host.execute(
                f"expr PyUnicode_AsUTF8((PyObject*)PyObject_Str((PyObject*)({variable})))"
            )
            self.io_manager.write(output)
        else:
            self.lldb_host.set_stdin(f"pp {variable}\n")

    def process_python_command_queue(self) -> None:
        if not self.lldb_host.is_stopped():
            return

        for i in self.python_command_queue:
            self.lldb_host.set_stdin(i + "\n")
        self.python_command_queue.clear()

    def print_variables(self) -> None:
        if self.lldb_host.is_stopped():
            output, _ = self.lldb_host.execute("vars")
            self.io_manager.write(output)
        else:
            self.lldb_host.set_stdin(
                'exec("from collections import deque; print(); deque((print(f\\"{k} = {v}\\") for k, v in locals().items() if ((not k.startswith(\\"_\\"))) and (k != \\"deque\\")), maxlen=1) and None")\n'
            )
