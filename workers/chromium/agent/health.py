from pathlib import Path

import psutil


def _cgroup_bytes(path: str) -> float | None:
    p = Path(path)
    if not p.exists():
        return None
    raw = p.read_text().strip()
    if raw.isdigit():
        return int(raw) / (1024 * 1024)
    return None


def metrics() -> dict:
    mem = psutil.virtual_memory()
    used = _cgroup_bytes("/sys/fs/cgroup/memory.current") or mem.used / (1024 * 1024)
    limit = _cgroup_bytes("/sys/fs/cgroup/memory.max")
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "ram_mb": used,
        "ram_limit_mb": limit,
    }
