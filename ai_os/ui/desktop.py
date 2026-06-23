"""Salmon AI OS desktop — tabbed TUI with animated boot."""
from __future__ import annotations
import asyncio

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Input, RichLog, Static, TabbedContent, TabPane
from rich.text import Text

from ..core.filesystem import VirtualFS
from ..core.process_registry import ProcessRegistry
from ..ai.assistant import AIAssistant
from ..apps.shell import Shell
from ..apps.terminal import TerminalApp
from ..apps.file_browser import FileBrowser
from ..apps.editor import EditorApp
from ..apps.aria_chat import ARIAChatApp
from ..apps.process_manager import ProcessManager

# ── boot animation data ────────────────────────────────────────────────────────

FISH_R = "><(((°>"
FISH_L = "<°)))><"
SWIM_WIDTH = 60
SWIM_CONFIGS = [(3, 0, 1), (2, 18, -1), (4, 10, 1), (2, 35, -1), (3, 25, 1)]

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


def _swim_frame(tick: int) -> Text:
    t = Text()
    t.append("\n" * 2)
    colors = ["salmon1", "orange_red1", "dark_orange", "orange1", "salmon1"]
    for i, (speed, offset, direction) in enumerate(SWIM_CONFIGS):
        fish = FISH_R if direction == 1 else FISH_L
        flen = len(fish)
        period = SWIM_WIDTH + flen
        pos = (offset + tick * speed) % period
        if direction == -1:
            pos = period - pos - flen
        line = " " * max(0, pos) + fish
        t.append(line[:SWIM_WIDTH] + "\n", style=f"bold {colors[i]}")
    t.append("\n")
    return t


def _banner_frame(lines_shown: int, msgs_shown: int) -> Text:
    t = Text()
    t.append("\n")
    for i, line in enumerate(BANNER_LINES):
        t.append((line + "\n") if i < lines_shown else "\n", style="bold salmon1")
    t.append("\n")
    for msg in BOOT_MESSAGES[:msgs_shown]:
        t.append_text(Text.from_markup(msg + "\n"))
    return t


# ── widgets ────────────────────────────────────────────────────────────────────

class StatusBar(Static):
    cwd = reactive("/")

    def render(self) -> Text:
        t = Text()
        t.append(" 🐟 SALMON AI OS ", style="bold white on dark_red")
        t.append(f" {self.cwd} ", style="white on grey23")
        t.append(" ARIA online ", style="bold green on grey15")
        return t


class BootDisplay(Static):
    pass


# ── main app ───────────────────────────────────────────────────────────────────

class Desktop(App):
    CSS = """
    Screen { background: #0d0d1a; }

    StatusBar { dock: top; height: 1; }

    BootDisplay {
        height: 1fr;
        content-align: center middle;
        background: #050510;
        padding: 2 4;
    }

    TabbedContent { height: 1fr; display: none; }
    TabbedContent.ready { display: block; }

    TabPane { height: 1fr; padding: 0; }

    Input {
        background: #0a0a20;
        border: round #1e3a5f;
        color: #e0e0ff;
    }
    Input:focus { border: round #00bfff; }

    Footer { background: #0a0a20; }
    """

    BINDINGS = [
        Binding("ctrl+c",     "quit",           "Quit"),
        Binding("ctrl+1",     "switch_tab('tab-terminal')", "Terminal",  show=False),
        Binding("ctrl+2",     "switch_tab('tab-files')",    "Files",     show=False),
        Binding("ctrl+3",     "switch_tab('tab-editor')",   "Editor",    show=False),
        Binding("ctrl+4",     "switch_tab('tab-aria')",     "ARIA Chat", show=False),
        Binding("ctrl+5",     "switch_tab('tab-procs')",   "Processes", show=False),
        Binding("ctrl+r",     "reset_aria",     "Reset ARIA"),
        Binding("ctrl+l",     "clear_terminal", "Clear"),
    ]

    def __init__(self):
        super().__init__()
        self.fs    = VirtualFS()
        self.ai    = AIAssistant()
        self.procs = ProcessRegistry()
        self.shell = Shell(self.fs, self.ai, self.procs)

    def compose(self) -> ComposeResult:
        yield StatusBar()
        yield BootDisplay()
        with TabbedContent(id="tabs"):
            with TabPane("  Terminal ", id="tab-terminal"):
                yield TerminalApp()
            with TabPane("  Files ", id="tab-files"):
                yield FileBrowser()
            with TabPane("  Editor ", id="tab-editor"):
                yield EditorApp()
            with TabPane("  ARIA Chat ", id="tab-aria"):
                yield ARIAChatApp()
            with TabPane("  Processes ", id="tab-procs"):
                yield ProcessManager()
        yield Footer()

    def on_mount(self) -> None:
        asyncio.create_task(self._boot_animation())

    # ── boot animation ─────────────────────────────────────────────────────

    async def _boot_animation(self) -> None:
        display = self.query_one(BootDisplay)

        for tick in range(36):
            display.update(_swim_frame(tick))
            await asyncio.sleep(0.06)

        for n in range(1, len(BANNER_LINES) + 1):
            display.update(_banner_frame(n, 0))
            await asyncio.sleep(0.10)

        for m in range(1, len(BOOT_MESSAGES) + 1):
            display.update(_banner_frame(len(BANNER_LINES), m))
            await asyncio.sleep(0.12)

        for _ in range(3):
            display.update(_banner_frame(len(BANNER_LINES), len(BOOT_MESSAGES)))
            await asyncio.sleep(0.12)
            display.update(Text(""))
            await asyncio.sleep(0.08)

        display.remove()
        self.query_one(TabbedContent).add_class("ready")
        self.query_one(StatusBar).cwd = self.fs.cwd
        self.query_one("#tab-terminal TerminalApp Input").focus()

    # ── tab actions ────────────────────────────────────────────────────────

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        pane_id = event.pane.id if event.pane else None
        focus_map = {
            "tab-terminal": "#tab-terminal #terminal-input",
            "tab-files":    "#tab-files #fs-tree",
            "tab-editor":   "#tab-editor TextArea",
            "tab-aria":     "#tab-aria #chat-input",
            "tab-procs":    "#tab-procs #proc-table",
        }
        selector = focus_map.get(pane_id or "")
        if selector:
            try:
                self.query_one(selector).focus()
            except Exception:
                pass

    # ── global actions ─────────────────────────────────────────────────────

    def action_reset_aria(self) -> None:
        self.ai.reset()
        try:
            self.query_one("#chat-log", RichLog).write(
                Text.from_markup("[yellow]ARIA memory cleared.[/]")
            )
        except Exception:
            pass

    def action_clear_terminal(self) -> None:
        try:
            self.query_one("#terminal-log", RichLog).clear()
        except Exception:
            pass
