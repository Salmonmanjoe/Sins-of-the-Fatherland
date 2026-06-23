"""Virtual in-memory filesystem for AI OS."""
import time
from dataclasses import dataclass, field
from typing import Optional


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
        self._init_tree()

    def _init_tree(self):
        dirs = ["home/user", "home/user/documents", "home/user/downloads",
                "bin", "etc", "var/log", "tmp", "sys/ai"]
        for path in dirs:
            self.mkdir(path)

        self.write("etc/os-release",
                   "NAME=Salmon-AI-OS\nVERSION=0.1.0\nID=salmon-ai-os\nPRETTY_NAME=\"Salmon AI OS 0.1.0\"\n")
        self.write("etc/motd",
                   "Welcome to Salmon AI OS — powered by Claude.\nType 'help' to begin.\n")
        self.write("home/user/readme.txt",
                   "This is your home directory.\nFiles you create here persist during your session.\n")
        self.write("sys/ai/model.cfg",
                   "model=claude-sonnet-4-6\nmax_tokens=2048\ntemperature=1\n")

    def _resolve(self, path: str) -> list[str]:
        if path.startswith("/"):
            parts = [p for p in path.split("/") if p]
        else:
            parts = self._cwd + [p for p in path.split("/") if p]
        resolved = []
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

    def mkdir(self, path: str) -> bool:
        parts = self._resolve(path)
        node = self.root
        for part in parts:
            if part not in node.children:
                node.children[part] = FSNode(part, is_dir=True, permissions="rwxr-xr-x")
            node = node.children[part]
            if not node.is_dir:
                return False
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
        parent.children[name] = FSNode(name, is_dir=False, content=content)
        return True

    def read(self, path: str) -> Optional[str]:
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node is None or node.is_dir:
            return None
        return node.content

    def delete(self, path: str) -> bool:
        parts = self._resolve(path)
        if not parts:
            return False
        parent = self._get_node(parts[:-1])
        name = parts[-1]
        if parent and name in parent.children:
            del parent.children[name]
            return True
        return False

    def listdir(self, path: str = ".") -> Optional[list[tuple[str, bool]]]:
        parts = self._resolve(path)
        node = self._get_node(parts)
        if node is None or not node.is_dir:
            return None
        return [(name, child.is_dir) for name, child in sorted(node.children.items())]

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
