import os
import sys
from shutil import which

from jupyter_server.extension.application import ExtensionApp
from traitlets import Type

from . import api_handlers
from . import handlers
from .terminalmanager import TerminalManager


class TerminalsExtensionApp(ExtensionApp):

    name = "jupyter_server_terminals"

    terminal_manager_class = Type(
        default_value=TerminalManager, help="The terminal manager class to use."
    ).tag(config=True)

    def initialize_settings(self):
        self.initialize_configurables()

    def initialize_configurables(self):
        if os.name == "nt":
            default_shell = "powershell.exe"
        else:
            default_shell = which("sh")
        shell_override = self.serverapp.terminado_settings.get("shell_command")
        shell = (
            [os.environ.get("SHELL") or default_shell] if shell_override is None else shell_override
        )
        # When the notebook server is not running in a terminal (e.g. when
        # it's launched by a JupyterHub spawner), it's likely that the user
        # environment hasn't been fully set up. In that case, run a login
        # shell to automatically source /etc/profile and the like, unless
        # the user has specifically set a preferred shell command.
        if os.name != "nt" and shell_override is None and not sys.stdout.isatty():
            shell.append("-l")

        self.terminal_manager = self.terminal_manager_class(
            shell_command=shell,
            extra_env={
                "JUPYTER_SERVER_ROOT": self.serverapp.root_dir,
                "JUPYTER_SERVER_URL": self.serverapp.connection_url,
            },
            parent=self.serverapp,
        )
        self.terminal_manager.log = self.serverapp.log

    def initialize_handlers(self):
        self.handlers.append(
            (
                r"/terminals/websocket/(\w+)",
                handlers.TermSocket,
                {"term_manager": self.terminal_manager},
            )
        )
        self.handlers.extend(api_handlers.default_handlers)
