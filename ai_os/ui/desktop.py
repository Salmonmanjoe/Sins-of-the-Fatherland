"""AI OS desktop — Textual TUI."""
from __future__ import annotations
import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Input, RichLog, Static
)
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel

from ..core.filesystem import VirtualFS
from ..ai.assistant import AIAssistant
from ..apps.shell import Shell

BOOT_LINES = [
    "[bold cyan]Salmon AI OS[/] v0.1.0 — booting...",
    "  [green]✓[/] Kernel loaded",
    "  [green]✓[/] Virtual filesystem mounted",
    "  [green]✓[/] ARIA AI module initialised",
    "  [green]✓[/] Shell ready",
    "",
    "[bold white]Welcome to Salmon AI OS.[/] Type [bold cyan]help[/] to get started.",
    "",
]

BANNER = r"""
                  ___
    ______       /o o \         ><(((°>
   /      \`~~~/       \    ><(((°>
  /  ~  ~  `--'  ~  ~  \      ><(((°>
 / ~ SALMON ~ AI ~ OS ~  \
<____~~~~~~~~~~~~~~~~~~~~>
      \    ><(((°>    /
       `~~~~~~~~~~~~~~'
"""


class StatusBar(Static):
    cwd = reactive("/")

    def render(self) -> Text:
        t = Text()
        t.append(" 🐟 SALMON AI OS ", style="bold white on dark_red")
        t.append(f" {self.cwd} ", style="white on grey23")
        t.append(" ARIA online ", style="bold green on grey15")
        return t


class Desktop(App):
    CSS = """
    Screen {
        background: #0d0d1a;
    }
    StatusBar {
        dock: top;
        height: 1;
    }
    #main-panel {
        height: 1fr;
    }
    #output-log {
        border: round #1e3a5f;
        background: #050510;
        height: 1fr;
        scrollbar-color: #1e3a5f;
    }
    #input-row {
        height: 3;
        align: left middle;
    }
    #prompt-label {
        width: auto;
        color: #00bfff;
        padding: 0 1;
    }
    Input {
        background: #0a0a20;
        border: round #1e3a5f;
        color: #e0e0ff;
        width: 1fr;
    }
    Input:focus {
        border: round #00bfff;
    }
    Footer {
        background: #0a0a20;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_log", "Clear"),
        Binding("ctrl+r", "reset_ai", "Reset AI"),
    ]

    def __init__(self):
        super().__init__()
        self.fs = VirtualFS()
        self.ai = AIAssistant()
        self.shell = Shell(self.fs, self.ai)
        self._pending_write: str | None = None
        self._history: list[str] = []
        self._hist_idx: int = -1

    def compose(self) -> ComposeResult:
        yield StatusBar()
        with Vertical(id="main-panel"):
            yield RichLog(id="output-log", markup=True, highlight=True, wrap=True)
            with Horizontal(id="input-row"):
                yield Static(">_", id="prompt-label")
                yield Input(placeholder="enter command…", id="cmd-input")
        yield Footer()

    def on_mount(self) -> None:
        self.call_after_refresh(self._boot)

    def _boot(self) -> None:
        log = self.query_one(RichLog)
        log.write(Text.from_markup(BANNER.strip(), style="bold salmon1"))
        for line in BOOT_LINES:
            log.write(Text.from_markup(line))
        self._sync_status()

    def _sync_status(self) -> None:
        self.query_one(StatusBar).cwd = self.fs.cwd

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        self.query_one(Input).clear()
        if not raw:
            return

        self._history.append(raw)
        self._hist_idx = -1

        log = self.query_one(RichLog)

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
        self._sync_status()

    async def _dispatch(self, raw: str, log: RichLog) -> None:
        # Run shell in thread so AI calls don't block the UI
        loop = asyncio.get_event_loop()
        output, clear = await loop.run_in_executor(None, self.shell.run, raw)

        if clear:
            log.clear()
            return

        if output == "__EXIT__":
            self.exit()
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

    def action_clear_log(self) -> None:
        self.query_one(RichLog).clear()

    def action_reset_ai(self) -> None:
        self.ai.reset()
        self.query_one(RichLog).write(
            Text.from_markup("[yellow]ARIA memory cleared.[/]")
        )
