"""lift-check all: every spec in specs/, in parallel, one line each and a summary."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .cli import SPECS

STATUSES = ("PASS", "FAIL", "SPEC", "UNSUPPORTED", "BUILD")
_IS_SPEC = re.compile(r"^FUNCTION\s*=", re.M)


def spec_names(prefix: str | None = None) -> list[str]:
    """Spec files: not `_`-prefixed, and with a FUNCTION (player_common.py is a helper)."""
    out = []
    for p in sorted(SPECS.glob("*.py")):
        if p.name.startswith("_") or (prefix and not p.stem.startswith(prefix)):
            continue
        if _IS_SPEC.search(p.read_text(errors="replace")):
            out.append(p.stem)
    return out


def run_one(name: str, extra: list[str], timeout: float) -> tuple[str, str, list[str], float]:
    """-> (status, its line, the rest of the output, seconds)"""
    t0 = time.monotonic()
    cmd = [sys.executable, "-m", "liftcheck", name, *extra]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=Path.cwd(), env=os.environ.copy())
    except subprocess.TimeoutExpired:
        return "TIMEOUT", f"TIMEOUT {name}: no result after {timeout:g} s", [], time.monotonic() - t0
    lines = (p.stdout + p.stderr).splitlines()
    for k, line in enumerate(lines):
        status = line.split(" ", 1)[0]
        if status in STATUSES and line[len(status) + 1:].startswith(name):
            return status, line, lines[k + 1:], time.monotonic() - t0
    tail = next((ln for ln in reversed(lines) if ln.strip()), f"exit code {p.returncode}")
    return "ERROR", f"ERROR {name}: {tail.strip()}", lines, time.monotonic() - t0


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="lift-check all", description=__doc__)
    ap.add_argument("--jobs", "-j", type=int, default=min(8, os.cpu_count() or 4))
    ap.add_argument("--filter", metavar="PREFIX", help="only specs whose name starts with PREFIX")
    ap.add_argument("--trials", type=int, help="override every spec's trial count")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--timeout", type=float, default=900, help="seconds per spec (default 900)")
    ap.add_argument("-v", "--verbose", action="store_true", help="print the context of non-PASS lines")
    args = ap.parse_args(argv)

    names = spec_names(args.filter)
    if not names:
        print(f"lift-check all: no specs" + (f" starting with '{args.filter}'" if args.filter else ""))
        return 2
    extra = []
    if args.trials is not None:
        extra += ["--trials", str(args.trials)]
    if args.seed is not None:
        extra += ["--seed", str(args.seed)]

    t0 = time.monotonic()
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = {pool.submit(run_one, n, extra, args.timeout): n for n in names}
        for fut in as_completed(futs):
            name = futs[fut]
            status, line, rest, secs = fut.result()
            results[name] = status
            print(f"{line}  [{secs:.1f}s]", flush=True)
            if args.verbose and status != "PASS":
                for ln in rest[:12]:
                    print(f"    {ln}", flush=True)

    bad = sorted(n for n, s in results.items() if s != "PASS")
    counts = {}
    for s in results.values():
        counts[s] = counts.get(s, 0) + 1
    summary = ", ".join(f"{counts[s]} {s}" for s in (*STATUSES, "TIMEOUT", "ERROR") if s in counts)
    print(f"lift-check all: {len(results)} specs in {time.monotonic() - t0:.0f} s: {summary}")
    for n in bad:
        print(f"  {results[n]:<11} {n}")
    return 1 if bad else 0
