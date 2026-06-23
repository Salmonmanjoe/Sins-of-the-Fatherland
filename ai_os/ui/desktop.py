"""AI OS desktop — Textual TUI."""
from __future__ import annotations
import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Input, RichLog, Static
from textual.reactive import reactive
from rich.text import Text

from ..core.filesystem import VirtualFS
from ..ai.assistant import AIAssistant
from ..apps.shell import Shell

# ── constants ─────────────────────────────────────────────────────────────────

FISH_R = "><(((°>"
FISH_L = "<°)))><"
SWIM_WIDTH = 60

BANNER_LINES = [
    r"                  ___                              ",
    r"    ______       /o o \         ><(((°>            ",
    r"   /      \`~~~/       \    ><(((°>                ",
    r"  /  ~  ~  `--'  ~  ~  \      ><(((°>             ",
    r" / ~ SALMON ~ AI ~ OS ~  \                         ",
    r"<____~~~~~~~~~~~~~~~~~~~~>                         ",
    r"      \    ><(((°>    /                            ",
    r"       `~~~~~~~~~~~~~~'                            ",
]

BOOT_MESSAGES = [
    "[bold cyan]Salmon AI OS[/] v0.1.0 — booting...",
    "  [green]✓[/] Kernel loaded",
    "  [green]✓[/] Virtual filesystem mounted",
    "  [green]✓[/] ARIA AI module initialised",
    "  [green]✓[/] Shell ready",
    "",
    "[bold white]Welcome to Salmon AI OS.[/] Type [bold cyan]help[/] to get started.",
    "",
]

# Fish swim configs: (speed, start_offset, direction)
# direction: +1 = left→right, -1 = right→left
SWIM_CONFIGS = [
    (3,  0,  1),
    (2, 18, -1),
    (4, 10,  1),
    (2, 35, -1),
    (3, 25,  1),
]

# ── helpers ───────────────────────────────────────────────────────────────────

def _swim_frame(tick: int) -> Text:
    """Build one frame of the swimming fish animation."""
    t = Text()
    t.append("\n" * 2)  # top padding
    fish_colors = ["salmon1", "orange_red1", "dark_orange", "orange1", "salmon1"]
    for i, (speed, offset, direction) in enumerate(SWIM_CONFIGS):
        fish = FISH_R if direction == 1 else FISH_L
        flen = len(fish)
        period = SWIM_WIDTH + flen
        pos = (offset + tick * speed) % period
        if direction == -1:
            pos = period - pos - flen
        line = " " * max(0, pos) + fish
        t.append(line[:SWIM_WIDTH] + "\n", style=f"bold {fish_colors[i]}")
    t.append("\n")
    return t


def _banner_frame(lines_shown: int, msgs_shown: int) -> Text:
    """Build frame with N banner lines + M boot messages revealed."""
    t = Text()
    t.append("\n")
    for i, line in enumerate(BANNER_LINES):
        if i < lines_shown:
            t.append(line + "\n", style="bold salmon1")
        else:
            t.append("\n")
    t.append("\n")
    for msg in BOOT_MESSAGES[:msgs_shown]:
        t.append_text(Text.from_markup(msg + "\n"))
    return t


# ── widgets ───────────────────────────────────────────────────────────────────

class StatusBar(Static):
    cwd = reactive("/")

    def render(self) -> Text:
        t = Text()
        t.append(" 🐟 SALMON AI OS ", style="bold white on dark_red")
        t.append(f" {self.cwd} ", style="white on grey23")
        t.append(" ARIA online ", style="bold green on grey15")
        return t


class BootDisplay(Static):
    """Full-screen animated boot canvas."""
    pass


# ── main app ──────────────────────────────────────────────────────────────────

class Desktop(App):
    CSS = """
    Screen {
        background: #0d0d1a;
    }
    StatusBar {
        dock: top;
        height: 1;
    }
    BootDisplay {
        height: 1fr;
        content-align: center middle;
        background: #050510;
        color: salmon;
        padding: 2 4;
    }
    #main-panel {
        height: 1fr;
        display: none;
    }
    #main-panel.ready {
        display: block;
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

    def compose(self) -> ComposeResult:
        yield StatusBar()
        yield BootDisplay()
        with Vertical(id="main-panel"):
            yield RichLog(id="output-log", markup=True, highlight=True, wrap=True)
            with Horizontal(id="input-row"):
                yield Static(">_", id="prompt-label")
                yield Input(placeholder="enter command…", id="cmd-input")
        yield Footer()

    def on_mount(self) -> None:
        asyncio.create_task(self._boot_animation())

    # ── animation ─────────────────────────────────────────────────────────────

    async def _boot_animation(self) -> None:
        display = self.query_one(BootDisplay)

        # Phase 1: fish swim across the screen
        for tick in range(36):
            display.update(_swim_frame(tick))
            await asyncio.sleep(0.06)

        # Phase 2: banner assembles line by line
        for n in range(1, len(BANNER_LINES) + 1):
            display.update(_banner_frame(n, 0))
            await asyncio.sleep(0.10)

        # Phase 3: boot messages appear one by one
        for m in range(1, len(BOOT_MESSAGES) + 1):
            display.update(_banner_frame(len(BANNER_LINES), m))
            await asyncio.sleep(0.12)

        # Phase 4: flash the banner three times then hand off
        for _ in range(3):
            display.update(_banner_frame(len(BANNER_LINES), len(BOOT_MESSAGES)))
            await asyncio.sleep(0.12)
            display.update(Text(""))
            await asyncio.sleep(0.08)

        # Transition to shell
        display.remove()
        log = self.query_one(RichLog)
        self.query_one("#main-panel").add_class("ready")
        log.write(_banner_frame(len(BANNER_LINES), len(BOOT_MESSAGES)))
        self.query_one(Input).focus()
        self._sync_status()

    # ── shell ─────────────────────────────────────────────────────────────────

    def _sync_status(self) -> None:
        self.query_one(StatusBar).cwd = self.fs.cwd

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        self.query_one(Input).clear()
        if not raw:
            return

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
        self.query_one(RichLog).write(Text.from_markup("[yellow]ARIA memory cleared.[/]"))
