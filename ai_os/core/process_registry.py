"""Virtual process registry for Salmon AI OS."""
from __future__ import annotations
import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .filesystem import VirtualFS


# ── data model ─────────────────────────────────────────────────────────────────

@dataclass
class Process:
    pid: int
    name: str
    owner: str
    description: str
    is_system: bool
    started: float = field(default_factory=time.time)
    _base_cpu: float = 0.0
    _base_mem: float = 0.0
    _status: str = "running"
    _task: Optional[asyncio.Task] = None

    def sample_cpu(self) -> float:
        return round(max(0.0, min(99.9, self._base_cpu + random.gauss(0, 0.6))), 1)

    def sample_mem(self) -> float:
        return round(max(0.1, self._base_mem + random.gauss(0, 0.12)), 1)

    @property
    def status(self) -> str:
        if self._task is not None and self._task.done():
            return "zombie"
        return self._status

    @property
    def uptime_str(self) -> str:
        s = int(time.time() - self.started)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


# ── background job coroutines ──────────────────────────────────────────────────

async def _job_log_writer(fs: "VirtualFS", pid: int) -> None:
    import datetime
    for tick in range(9_999):
        content = fs.read("/var/log/system.log") or ""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        content += f"[{ts}] PID {pid}: heartbeat #{tick + 1}\n"
        fs.write("/var/log/system.log", content[-4_000:])
        await asyncio.sleep(2)


async def _job_ticker(fs: "VirtualFS", pid: int) -> None:
    """Runs for 30 s then exits cleanly (demo of a finishing process)."""
    await asyncio.sleep(30)


async def _job_file_scanner(fs: "VirtualFS", pid: int) -> None:
    for tick in range(9_999):
        entries = fs.listdir("/home/user") or []
        lines = [f"=== scan #{tick + 1} — {len(entries)} entries ==="]
        for name, is_dir in entries:
            lines.append(f"  {'[DIR]' if is_dir else '[FIL]'} {name}")
        fs.write("/tmp/scan.txt", "\n".join(lines))
        await asyncio.sleep(5)


async def _job_aria_monitor(fs: "VirtualFS", pid: int) -> None:
    import datetime
    for tick in range(9_999):
        content = fs.read("/sys/ai/monitor.log") or ""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        content += f"[{ts}] ARIA alive — tick {tick + 1}\n"
        fs.write("/sys/ai/monitor.log", content[-3_000:])
        await asyncio.sleep(10)


async def _job_entropy_seed(fs: "VirtualFS", pid: int) -> None:
    import datetime
    for tick in range(9_999):
        val = random.getrandbits(256)
        content = fs.read("/dev/random") or ""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        content += f"[{ts}] {val:064x}\n"
        fs.write("/dev/random", content[-2_000:])
        await asyncio.sleep(3)


# ── job registry ───────────────────────────────────────────────────────────────

AVAILABLE_JOBS: dict[str, tuple[str, float, float]] = {
    "log-writer":    ("Writes heartbeats to /var/log/system.log",  1.2, 6.0),
    "ticker":        ("Runs for 30 s then exits cleanly",           0.1, 2.0),
    "file-scanner":  ("Scans /home/user → /tmp/scan.txt",           0.8, 4.5),
    "aria-monitor":  ("Monitors ARIA → /sys/ai/monitor.log",        1.5, 8.0),
    "entropy-seed":  ("Feeds entropy pool → /dev/random",           0.4, 3.2),
}

_JOB_COROS = {
    "log-writer":   _job_log_writer,
    "ticker":       _job_ticker,
    "file-scanner": _job_file_scanner,
    "aria-monitor": _job_aria_monitor,
    "entropy-seed": _job_entropy_seed,
}


# ── registry ───────────────────────────────────────────────────────────────────

class ProcessRegistry:
    def __init__(self) -> None:
        self._next_pid = 100
        self.processes: dict[int, Process] = {}
        self._boot_time = time.time()
        self._init_system_procs()

    def _init_system_procs(self) -> None:
        t = self._boot_time
        defs = [
            (1, "init",        "root", "System init daemon",          0.0,  2.1,  "sleeping"),
            (2, "vfs-daemon",  "root", "Virtual filesystem daemon",   0.1,  4.8,  "running"),
            (3, "aria-daemon", "root", "ARIA AI inference engine",    2.4,  68.4, "running"),
            (4, "shell",       "user", "Interactive shell session",   0.3,  3.1,  "running"),
            (5, "tab-manager", "root", "Window and tab compositor",   0.5,  5.6,  "running"),
        ]
        for pid, name, owner, desc, cpu, mem, status in defs:
            self.processes[pid] = Process(
                pid=pid, name=name, owner=owner, description=desc,
                is_system=True, started=t,
                _base_cpu=cpu, _base_mem=mem, _status=status,
            )

    def spawn(self, name: str, fs: "VirtualFS", owner: str = "user") -> tuple[int, str]:
        if name not in AVAILABLE_JOBS:
            opts = ", ".join(AVAILABLE_JOBS)
            return -1, f"Unknown: '{name}'. Available: {opts}"
        desc, base_cpu, base_mem = AVAILABLE_JOBS[name]
        pid = self._next_pid
        self._next_pid += 1
        coro = _JOB_COROS[name](fs, pid)
        task = asyncio.create_task(coro)
        self.processes[pid] = Process(
            pid=pid, name=name, owner=owner, description=desc,
            is_system=False, _base_cpu=base_cpu, _base_mem=base_mem,
            _status="running", _task=task,
        )
        return pid, f"[{pid}] {name} started"

    def kill(self, pid: int) -> tuple[bool, str]:
        proc = self.processes.get(pid)
        if proc is None:
            return False, f"kill: ({pid}) no such process"
        if proc.is_system:
            return False, f"kill: ({pid}) Operation not permitted"
        if proc._task and not proc._task.done():
            proc._task.cancel()
        name = proc.name
        del self.processes[pid]
        return True, f"[{pid}] {name} terminated"

    def reap_zombies(self) -> list[int]:
        dead = [
            pid for pid, p in list(self.processes.items())
            if not p.is_system and p._task is not None and p._task.done()
        ]
        for pid in dead:
            del self.processes[pid]
        return dead

    def list_all(self) -> list[Process]:
        return [p for _, p in sorted(self.processes.items())]

    @property
    def total_cpu(self) -> float:
        return round(sum(p._base_cpu for p in self.processes.values()), 1)

    @property
    def total_mem(self) -> float:
        return round(sum(p._base_mem for p in self.processes.values()), 1)
