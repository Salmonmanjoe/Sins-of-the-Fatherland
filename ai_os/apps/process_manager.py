"""Process Manager tab widget."""
from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Static

from ..core.process_registry import AVAILABLE_JOBS

_STATUS_STYLE = {
    "running":  ("bold green",  "▶"),
    "sleeping": ("bold yellow", "~"),
    "zombie":   ("bold red",    "☠"),
}

_COL_LABELS = ("PID", "NAME", "STATUS", "CPU %", "MEM", "OWNER", "UPTIME", "DESCRIPTION")


class ProcessManager(Widget):
    DEFAULT_CSS = """
    ProcessManager { height: 1fr; }
    ProcessManager > Vertical { height: 1fr; }

    #proc-header {
        height: 1;
        background: #0a1a00;
        color: #88ff44;
        padding: 0 1;
    }
    #proc-table {
        height: 1fr;
        border: round #2a4a00;
        background: #050510;
    }
    #proc-summary {
        height: 1;
        background: #0a1a00;
        color: #aaffaa;
        padding: 0 1;
    }
    #proc-toolbar { height: 3; align: left middle; padding: 0 1; }
    #proc-input {
        width: 1fr;
        margin-right: 1;
        border: round #2a4a00;
    }
    #proc-input:focus { border: round #88ff44; }
    #btn-launch { min-width: 12; margin-right: 1; }
    #btn-kill   { min-width: 10; }
    """

    def __init__(self) -> None:
        super().__init__()
        self._col_keys: list = []

    @property
    def procs(self):
        return self.app.procs

    def compose(self) -> ComposeResult:
        jobs = ", ".join(AVAILABLE_JOBS)
        with Vertical():
            yield Static(
                f"  ⚙  Process Manager   [dim]jobs: {jobs}[/]",
                id="proc-header", markup=True,
            )
            yield DataTable(id="proc-table", cursor_type="row", zebra_stripes=True)
            yield Static("", id="proc-summary", markup=True)
            with Horizontal(id="proc-toolbar"):
                yield Input(
                    placeholder="job name  (log-writer | ticker | file-scanner | aria-monitor | entropy-seed)",
                    id="proc-input",
                )
                yield Button("▶ Launch", id="btn-launch", variant="success")
                yield Button("✕ Kill",   id="btn-kill",   variant="error")

    def on_mount(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        self._col_keys = table.add_columns(*_COL_LABELS)
        self._rebuild()
        self.set_interval(1.0, self._tick)

    # ── row helpers ────────────────────────────────────────────────────────

    def _make_row(self, proc) -> list[Text]:
        status = proc.status
        style, icon = _STATUS_STYLE.get(status, ("white", "?"))
        return [
            Text(str(proc.pid),             style="dim cyan"),
            Text(proc.name,                 style="bold #88ff44" if proc.is_system else "bold white"),
            Text(f"{icon} {status}",        style=style),
            Text(f"{proc.sample_cpu():.1f}", style="yellow"),
            Text(f"{proc.sample_mem():.1f} MB", style="cyan"),
            Text(proc.owner,                style="magenta" if proc.owner == "root" else "white"),
            Text(proc.uptime_str,           style="dim"),
            Text(proc.description,          style="dim"),
        ]

    def _rebuild(self) -> None:
        table = self.query_one("#proc-table", DataTable)
        cursor = table.cursor_row
        table.clear()
        for pid, proc in sorted(self.procs.processes.items()):
            table.add_row(*self._make_row(proc), key=str(pid))
        if table.row_count > 0:
            table.move_cursor(row=min(cursor, table.row_count - 1))
        self._update_summary()

    def _tick(self) -> None:
        reaped = self.procs.reap_zombies()
        table  = self.query_one("#proc-table", DataTable)

        current_pids  = {str(pid) for pid in self.procs.processes}
        existing_pids = {str(rk) for rk in table.rows}   # RowKey.__str__ == its value

        added   = current_pids - existing_pids
        removed = existing_pids - current_pids

        if added or removed:
            self._rebuild()
            return

        # smooth cell-level update for existing rows
        for pid_str in current_pids:
            proc = self.procs.processes[int(pid_str)]
            row  = self._make_row(proc)
            for col_key, val in zip(self._col_keys, row):
                try:
                    table.update_cell(pid_str, col_key, val, update_width=False)
                except Exception:
                    pass

        self._update_summary()

    def _update_summary(self) -> None:
        n    = len(self.procs.processes)
        user = sum(1 for p in self.procs.processes.values() if not p.is_system)
        cpu  = self.procs.total_cpu
        mem  = self.procs.total_mem
        self.query_one("#proc-summary", Static).update(
            f"  [bold]Processes:[/] {n} total, {user} user  │  "
            f"[bold]CPU:[/] {cpu:.1f}%  │  [bold]MEM:[/] {mem:.1f} MB"
        )

    # ── events ─────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-launch":
            self._launch()
        elif event.button.id == "btn-kill":
            self._kill_selected()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "proc-input":
            event.stop()
            self._launch()

    def _launch(self) -> None:
        name = self.query_one("#proc-input", Input).value.strip()
        if not name:
            self.notify("Enter a job name", severity="warning")
            return
        pid, msg = self.procs.spawn(name, self.app.fs)
        if pid < 0:
            self.notify(msg, severity="error")
        else:
            self.query_one("#proc-input", Input).clear()
            self.notify(msg, severity="information")
            self._rebuild()

    def _kill_selected(self) -> None:
        table      = self.query_one("#proc-table", DataTable)
        sorted_pids = sorted(self.procs.processes.keys())
        idx        = table.cursor_row
        if idx < 0 or idx >= len(sorted_pids):
            self.notify("Select a process first", severity="warning")
            return
        pid = sorted_pids[idx]
        ok, msg = self.procs.kill(pid)
        self.notify(msg, severity="information" if ok else "error")
