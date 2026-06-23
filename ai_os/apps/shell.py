"""AI OS shell — interprets built-in commands and falls back to ARIA."""
from __future__ import annotations
import shlex
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.filesystem import VirtualFS
    from ..ai.assistant import AIAssistant
    from ..core.process_registry import ProcessRegistry


HELP_TEXT = """
AI OS Shell — built-in commands
────────────────────────────────
  help              Show this help
  ls [path]         List directory
  cd <path>         Change directory
  pwd               Print working dir
  cat <file>        Read a file
  write <file>      Write/create a file (interactive)
  rm <file>         Delete a file
  mkdir <dir>       Create a directory
  echo <text>       Print text
  clear             Clear the screen
  ps                List running processes
  run <job>         Spawn a background job
  kill <pid>        Terminate a user process
  jobs              Show available background jobs
  ai <prompt>       Talk to ARIA (AI assistant)
  ai reset          Reset ARIA conversation history
  sysinfo           Show OS info
  exit / quit       Exit AI OS
────────────────────────────────
Any unrecognised command is forwarded to ARIA.
"""


class Shell:
    def __init__(self, fs: "VirtualFS", ai: "AIAssistant",
                 procs: "ProcessRegistry | None" = None):
        self.fs = fs
        self.ai = ai
        self.procs = procs

    def run(self, raw: str) -> tuple[str, bool]:
        """Process a command. Returns (output, should_clear)."""
        raw = raw.strip()
        if not raw:
            return "", False

        try:
            parts = shlex.split(raw)
        except ValueError as e:
            return f"parse error: {e}", False

        cmd, args = parts[0].lower(), parts[1:]

        if cmd in ("exit", "quit"):
            return "__EXIT__", False
        if cmd == "clear":
            return "", True
        if cmd == "help":
            return HELP_TEXT, False
        if cmd == "pwd":
            return self.fs.cwd, False
        if cmd == "echo":
            return " ".join(args), False
        if cmd == "sysinfo":
            return self._sysinfo(), False
        if cmd == "ls":
            return self._ls(args[0] if args else "."), False
        if cmd == "cd":
            return self._cd(args[0] if args else "/home/user"), False
        if cmd == "cat":
            return self._cat(args[0] if args else ""), False
        if cmd == "mkdir":
            return self._mkdir(args[0] if args else ""), False
        if cmd == "rm":
            return self._rm(args[0] if args else ""), False
        if cmd == "write":
            return "__WRITE__:" + (args[0] if args else ""), False
        if cmd == "ai":
            return self._ai(args), False
        if cmd == "ps":
            return self._ps(), False
        if cmd == "run":
            return self._run(args[0] if args else ""), False
        if cmd == "kill":
            return self._kill(args[0] if args else ""), False
        if cmd == "jobs":
            return self._jobs(), False

        # Unknown command → forward to ARIA
        return self._ai([raw]), False

    # ── built-in implementations ──────────────────────────────────────────

    def _ls(self, path: str) -> str:
        entries = self.fs.listdir(path)
        if entries is None:
            return f"ls: {path}: no such directory"
        if not entries:
            return "(empty)"
        lines = []
        for name, is_dir in entries:
            lines.append(f"{'[DIR] ' if is_dir else '      '}{name}")
        return "\n".join(lines)

    def _cd(self, path: str) -> str:
        if not self.fs.chdir(path):
            return f"cd: {path}: no such directory"
        return ""

    def _cat(self, path: str) -> str:
        if not path:
            return "cat: missing file argument"
        content = self.fs.read(path)
        if content is None:
            return f"cat: {path}: no such file"
        return content

    def _mkdir(self, path: str) -> str:
        if not path:
            return "mkdir: missing argument"
        return "" if self.fs.mkdir(path) else f"mkdir: {path}: failed"

    def _rm(self, path: str) -> str:
        if not path:
            return "rm: missing argument"
        return "" if self.fs.delete(path) else f"rm: {path}: no such file"

    def _ai(self, args: list[str]) -> str:
        if not args:
            return "Usage: ai <prompt>  or  ai reset"
        if args[0].lower() == "reset":
            self.ai.reset()
            return "ARIA conversation history cleared."
        prompt = " ".join(args)
        try:
            return self.ai.chat(prompt)
        except Exception as e:
            return f"ARIA error: {e}"

    def _ps(self) -> str:
        if not self.procs:
            return "ps: process registry unavailable"
        lines = [f"{'PID':>5}  {'NAME':<16}  {'STATUS':<10}  {'CPU%':>5}  {'MEM':>8}  OWNER"]
        lines.append("─" * 62)
        for p in self.procs.list_all():
            lines.append(
                f"{p.pid:>5}  {p.name:<16}  {p.status:<10}  "
                f"{p.sample_cpu():>4.1f}%  {p.sample_mem():>5.1f} MB  {p.owner}"
            )
        return "\n".join(lines)

    def _run(self, name: str) -> str:
        if not name:
            return "run: missing job name. Try: run log-writer"
        if not self.procs:
            return "run: process registry unavailable"
        _, msg = self.procs.spawn(name, self.fs)
        return msg

    def _kill(self, arg: str) -> str:
        if not arg:
            return "kill: missing PID"
        if not self.procs:
            return "kill: process registry unavailable"
        try:
            pid = int(arg)
        except ValueError:
            return f"kill: '{arg}' is not a PID"
        _, msg = self.procs.kill(pid)
        return msg

    def _jobs(self) -> str:
        from ..core.process_registry import AVAILABLE_JOBS
        lines = ["Available background jobs:", "─" * 46]
        for name, (desc, cpu, mem) in AVAILABLE_JOBS.items():
            lines.append(f"  {name:<16}  {desc}")
        return "\n".join(lines)

    def _sysinfo(self) -> str:
        content = self.fs.read("etc/os-release") or ""
        info = dict(line.split("=", 1) for line in content.splitlines() if "=" in line)
        model_cfg = self.fs.read("sys/ai/model.cfg") or ""
        mcfg = dict(line.split("=", 1) for line in model_cfg.splitlines() if "=" in line)
        return (
            f"  OS:      {info.get('PRETTY_NAME', 'AI OS')}\n"
            f"  Shell:   AI OS Shell v0.1\n"
            f"  AI:      ARIA ({mcfg.get('model', 'claude')})\n"
            f"  CWD:     {self.fs.cwd}"
        )
