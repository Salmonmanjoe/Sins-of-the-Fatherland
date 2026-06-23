"""Terminal tab widget."""
from __future__ import annotations
import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Input, RichLog, Static
from rich.text import Text

from .shell import Shell


class TerminalApp(Widget):
    DEFAULT_CSS = """
    TerminalApp { height: 1fr; }
    TerminalApp > Vertical { height: 1fr; }
    #terminal-log {
        border: round #1e3a5f;
        background: #050510;
        height: 1fr;
    }
    #terminal-input-row { height: 3; align: left middle; }
    #terminal-prompt { width: auto; color: #00bfff; padding: 0 1; }
    """

    def __init__(self):
        super().__init__()
        self._pending_write: str | None = None

    @property
    def fs(self):
        return self.app.fs

    @property
    def shell(self) -> Shell:
        return self.app.shell

    def compose(self) -> ComposeResult:
        with Vertical():
            yield RichLog(id="terminal-log", markup=True, highlight=True, wrap=True)
            with Horizontal(id="terminal-input-row"):
                yield Static(">_", id="terminal-prompt")
                yield Input(placeholder="enter command…", id="terminal-input")

    def on_mount(self) -> None:
        self.query_one("#terminal-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "terminal-input":
            return
        event.stop()
        raw = event.value.strip()
        self.query_one("#terminal-input", Input).clear()
        if not raw:
            return

        log = self.query_one("#terminal-log", RichLog)

        # handle pending file write
        if self._pending_write is not None:
            path = self._pending_write
            self._pending_write = None
            ok = self.fs.write(path, raw)
            log.write(Text.from_markup(
                f"  [green]✓ written:[/] {path}" if ok else f"  [red]✗ write failed:[/] {path}"
            ))
            return

        log.write(Text.from_markup(f"[bold cyan]>[/] [white]{raw}[/]"))
        await self._dispatch(raw, log)
        self.app.query_one("StatusBar").cwd = self.fs.cwd

    async def _dispatch(self, raw: str, log: RichLog) -> None:
        loop = asyncio.get_event_loop()
        output, clear = await loop.run_in_executor(None, self.shell.run, raw)

        if clear:
            log.clear()
            return
        if output == "__EXIT__":
            self.app.exit()
            return
        if isinstance(output, str) and output.startswith("__WRITE__:"):
            path = output[len("__WRITE__:"):]
            if not path:
                log.write(Text.from_markup("[red]write: missing filename[/]"))
                return
            self._pending_write = path
            log.write(Text.from_markup(
                f"[yellow]Enter content for[/] [bold]{path}[/] [yellow]then press Enter:[/]"
            ))
            return
        if output:
            log.write(Text.from_markup(output))

    def write_line(self, markup: str) -> None:
        self.query_one("#terminal-log", RichLog).write(Text.from_markup(markup))

    def clear(self) -> None:
        self.query_one("#terminal-log", RichLog).clear()
