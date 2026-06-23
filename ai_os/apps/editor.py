"""Text editor tab widget."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, TextArea
from rich.text import Text


class EditorApp(Widget):
    DEFAULT_CSS = """
    EditorApp { height: 1fr; }
    EditorApp > Vertical { height: 1fr; }
    #editor-toolbar {
        height: 3;
        align: left middle;
        padding: 0 1;
    }
    #editor-path { width: 1fr; margin-right: 1; }
    #editor-toolbar Button { min-width: 8; margin-right: 1; }
    #editor-status {
        height: 1;
        background: #1e3a5f;
        color: #aaaacc;
        padding: 0 1;
    }
    TextArea {
        height: 1fr;
        border: round #1e3a5f;
        background: #050510;
    }
    TextArea:focus { border: round #00bfff; }
    """

    def __init__(self):
        super().__init__()
        self._current_path: str | None = None

    @property
    def fs(self):
        return self.app.fs

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="editor-toolbar"):
                yield Input(placeholder="file path…", id="editor-path")
                yield Button("Open", id="btn-open", variant="primary")
                yield Button("New",  id="btn-new",  variant="default")
                yield Button("Save", id="btn-save", variant="success")
            yield TextArea("", id="editor-area")
            yield Input(id="editor-status",
                        placeholder="[no file open]",
                        disabled=True)

    def _set_status(self, msg: str) -> None:
        self.query_one("#editor-status", Input).placeholder = msg

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-open":
            self._open_file()
        elif bid == "btn-new":
            self._new_file()
        elif bid == "btn-save":
            self._save_file()

    def _open_file(self) -> None:
        path = self.query_one("#editor-path", Input).value.strip()
        if not path:
            self._set_status("⚠  Enter a file path first")
            return
        content = self.fs.read(path)
        if content is None:
            self._set_status(f"✗  Not found: {path}")
            return
        self._current_path = path
        ta = self.query_one("#editor-area", TextArea)
        ta.load_text(content)
        ta.focus()
        self._set_status(f"✓  Opened: {path}")

    def _new_file(self) -> None:
        path = self.query_one("#editor-path", Input).value.strip()
        self._current_path = path or None
        ta = self.query_one("#editor-area", TextArea)
        ta.load_text("")
        ta.focus()
        self._set_status(f"New file: {path or '(unsaved)'}")

    def _save_file(self) -> None:
        path = (self.query_one("#editor-path", Input).value.strip()
                or self._current_path)
        if not path:
            self._set_status("⚠  No file path — enter one above")
            return
        content = self.query_one("#editor-area", TextArea).text
        if self.fs.write(path, content):
            self._current_path = path
            self.query_one("#editor-path", Input).value = path
            self._set_status(f"✓  Saved: {path}")
        else:
            self._set_status(f"✗  Save failed: {path}")
