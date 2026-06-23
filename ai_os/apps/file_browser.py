"""File Browser tab widget."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, RichLog, Static, Tree
from textual.widgets.tree import TreeNode
from rich.text import Text


class FileBrowser(Widget):
    DEFAULT_CSS = """
    FileBrowser { height: 1fr; }
    FileBrowser > Vertical { height: 1fr; }
    #browser-toolbar { height: 3; align: right middle; padding: 0 1; }
    #browser-toolbar Button { min-width: 10; }
    #browser-split { height: 1fr; }
    #fs-tree {
        width: 32;
        border: round #1e3a5f;
        background: #050510;
    }
    #file-preview {
        border: round #1e3a5f;
        background: #050510;
        width: 1fr;
    }
    #preview-header {
        height: 1;
        background: #1e3a5f;
        color: #00bfff;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._current_file: str | None = None

    @property
    def fs(self):
        return self.app.fs

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="browser-toolbar"):
                yield Static("[bold]File Browser[/]  [dim]click a file to preview[/]",
                             markup=True, id="browser-hint")
                yield Button("⟳ Refresh", id="btn-refresh", variant="default")
            with Horizontal(id="browser-split"):
                yield Tree("/", id="fs-tree")
                with Vertical():
                    yield Static("", id="preview-header", markup=True)
                    yield RichLog(id="file-preview", markup=True, highlight=True, wrap=True)

    def on_mount(self) -> None:
        self._build_tree()

    def _build_tree(self) -> None:
        tree = self.query_one("#fs-tree", Tree)
        tree.clear()
        root = tree.root
        root.set_label("📂 /")
        root.data = {"path": "/", "is_dir": True}
        self._populate(root, "/")
        root.expand()

    def _populate(self, node: TreeNode, fs_path: str, depth: int = 0) -> None:
        if depth > 6:
            return
        entries = self.fs.listdir(fs_path) or []
        dirs  = [(n, p) for n, p in entries if p]
        files = [(n, p) for n, p in entries if not p]
        for name, _ in sorted(dirs):
            full = (fs_path.rstrip("/") + "/" + name)
            child = node.add(f"📁 {name}", data={"path": full, "is_dir": True}, expand=False)
            self._populate(child, full, depth + 1)
        for name, _ in sorted(files):
            full = (fs_path.rstrip("/") + "/" + name)
            node.add_leaf(f"📄 {name}", data={"path": full, "is_dir": False})

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data
        if not data or data.get("is_dir"):
            return
        path: str = data["path"]
        content = self.fs.read(path)
        header = self.query_one("#preview-header", Static)
        preview = self.query_one("#file-preview", RichLog)
        header.update(f"[bold cyan]{path}[/]")
        preview.clear()
        if content is None:
            preview.write(Text.from_markup("[red](unreadable)[/]"))
        elif content.strip() == "":
            preview.write(Text.from_markup("[dim](empty file)[/]"))
        else:
            preview.write(content)
        self._current_file = path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh":
            self.refresh_tree()

    def refresh_tree(self) -> None:
        self._build_tree()
        self.query_one("#preview-header", Static).update("")
        self.query_one("#file-preview", RichLog).clear()
        self._current_file = None
