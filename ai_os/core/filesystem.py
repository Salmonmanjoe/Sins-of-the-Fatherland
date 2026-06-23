"""Virtual in-memory filesystem for AI OS — with JSON persistence."""
import json
import pathlib
import time
from dataclasses import dataclass, field
from typing import Optional

FS_SAVE_PATH = pathlib.Path.home() / ".salmon_ai_os" / "filesystem.json"


@dataclass
class FSNode:
    name: str
    is_dir: bool
    content: str = ""
    children: dict = field(default_factory=dict)
    created: float = field(default_factory=time.time)
    modified: float = field(default_factory=time.time)
    permissions: str = "rw-r--r--"


class VirtualFS:
    def __init__(self):
        self.root = FSNode("/", is_dir=True, permissions="rwxr-xr-x")
        self._cwd: list[str] = []
        if not self.load(FS_SAVE_PATH):
            self._init_tree()

    # ── default tree ───────────────────────────────────────────────────────

    def _init_tree(self):
        for path in ["home/user", "home/user/documents", "home/user/downloads",
                     "bin", "etc", "var/log", "tmp", "sys/ai"]:
            self.mkdir(path)
        self.write("etc/os-release",
                   'NAME=Salmon-AI-OS\nVERSION=0.1.0\nID=salmon-ai-os\nPRETTY_NAME="Salmon AI OS 0.1.0"\n')
        self.write("etc/motd",
                   "Welcome to Salmon AI OS — powered by Claude.\nType 'help' to begin.\n")
        self.write("home/user/readme.txt",
                   "This is your home directory.\nFiles you create here persist between sessions.\n")
        self.write("sys/ai/model.cfg",
                   "model=claude-sonnet-4-6\nmax_tokens=2048\ntemperature=1\n")

    # ── serialisation ──────────────────────────────────────────────────────

    def _node_to_dict(self, node: FSNode) -> dict:
        d: dict = {
            "name": node.name,
            "is_dir": node.is_dir,
            "content": node.content,
            "permissions": node.permissions,
            "created": node.created,
            "modified": node.modified,
        }
        if node.is_dir:
            d["children"] = {k: self._node_to_dict(v) for k, v in node.children.items()}
        return d

    def _dict_to_node(self, d: dict) -> FSNode:
        node = FSNode(
            name=d["name"],
            is_dir=d["is_dir"],
            content=d.get("content", ""),
            permissions=d.get("permissions", "rw-r--r--"),
            created=d.get("created", time.time()),
            modified=d.get("modified", time.time()),
        )
        if node.is_dir:
            for k, v in d.get("children", {}).items():
                node.children[k] = self._dict_to_node(v)
        return node

    def save(self, path=FS_SAVE_PATH) -> bool:
        try:
            p = pathlib.Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            data = {"root": self._node_to_dict(self.root), "cwd": self._cwd}
            p.write_text(json.dumps(data, indent=2))
            return True
        except Exception:
            return False

    def load(self, path=FS_SAVE_PATH) -> bool:
        try:
            p = pathlib.Path(path)
            if not p.exists():
                return False
            data = json.loads(p.read_text())
            self.root = self._dict_to_node(data["root"])
            self._cwd = data.get("cwd", [])
            return True
        except Exception:
            return False

    # ── path resolution ────────────────────────────────────────────────────

    def _resolve(self, path: str) -> list[str]:
        parts = [p for p in path.split("/") if p] if path.startswith("/") else \
                self._cwd + [p for p in path.split("/") if p]
        resolved: list[str] = []
        for p in parts:
            if p == "..":
                if resolved:
                    resolved.pop()
            elif p != ".":
                resolved.append(p)
        return resolved

    def _get_node(self, parts: list[str]) -> Optional[FSNode]:
        node = self.root
        for part in parts:
            if not node.is_dir or part not in node.children:
                return None
            node = node.children[part]
        return node

    # ── mutations (all auto-save) ──────────────────────────────────────────

    def mkdir(self, path: str) -> bool:
        parts = self._resolve(path)
        node = self.root
        for part in parts:
            if part not in node.children:
                node.children[part] = FSNode(part, is_dir=True, permissions="rwxr-xr-x")
            node = node.children[part]
            if not node.is_dir:
                return False
        self.save()
        return True

    def write(self, path: str, content: str) -> bool:
        parts = self._resolve(path)
        if not parts:
            return False
        parent = self._get_node(parts[:-1])
        if parent is None or not parent.is_dir:
            return False
        name = parts[-1]
        if name in parent.children and parent.children[name].is_dir:
            return False
        now = time.time()
        parent.children[name] = FSNode(name, is_dir=False, content=content,
                                       created=now, modified=now)
        self.save()
        return True

    def delete(self, path: str) -> bool:
        parts = self._resolve(path)
        if not parts:
            return False
        parent = self._get_node(parts[:-1])
        name = parts[-1]
        if parent and name in parent.children:
            del parent.children[name]
            self.save()
            return True
        return False

    # ── reads ──────────────────────────────────────────────────────────────

    def read(self, path: str) -> Optional[str]:
        node = self._get_node(self._resolve(path))
        return None if node is None or node.is_dir else node.content

    def listdir(self, path: str = ".") -> Optional[list[tuple[str, bool]]]:
        node = self._get_node(self._resolve(path))
        if node is None or not node.is_dir:
            return None
        return [(n, c.is_dir) for n, c in sorted(node.children.items())]

    def exists(self, path: str) -> bool:
        return self._get_node(self._resolve(path)) is not None

    def is_dir(self, path: str) -> bool:
        node = self._get_node(self._resolve(path))
        return node is not None and node.is_dir

    def chdir(self, path: str) -> bool:
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node and node.is_dir:
            self._cwd = parts
            return True
        return False

    @property
    def cwd(self) -> str:
        return "/" + "/".join(self._cwd) if self._cwd else "/"
