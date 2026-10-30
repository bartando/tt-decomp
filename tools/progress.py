#!/usr/bin/env python3
"""How far the decomp is: verified / lifted / known wrong / todo.

    python3 tools/progress.py                     # runs lift-check all first (~1min)
    python3 tools/progress.py --log lc.log        # reuse a `lift-check all` output
    python3 tools/progress.py --hot hot.tsv       # also the split over what a match runs

verified:   a lift-check spec for it passes
lifted:     has a `@ 0x...` marker in src/ but no passing spec
wrong:      named in KNOWN_WRONG_LIFTS.md (overrides the two above)
todo:       nothing yet

--hot takes ttrecomp's tools/rank_hot_functions.py output and weights each
function by its score (calls/s * size), so "verified 30%" there means 30% of the
work the game does in a match runs through verified lifts.
"""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "tools/lift-check/specs"
ORDER = ("verified", "lifted", "wrong", "todo")


def all_functions():
    pattern = re.compile(r"\.text:0x([0-9A-Fa-f]{8}); // type:function")
    text = (ROOT / "config/434C4803/symbols.txt").read_text()
    return {int(address, 16) for address in pattern.findall(text)}


def lifted():
    found = set()
    for path in (ROOT / "src").rglob("*"):
        if path.suffix in (".c", ".cpp"):
            text = path.read_text(errors="ignore")
            found.update(int(a, 16) for a in re.findall(r"@\s*0x(82[0-9A-Fa-f]{6})", text))
    return found


def verified(log):
    if log is None:
        log = subprocess.run([str(ROOT / "tools/lift-check/lift-check"), "all", "--jobs", "8"],
                             cwd=ROOT, capture_output=True, text=True).stdout
    found = set()
    for name in re.findall(r"^PASS (\S+):", log, re.M):
        match = re.search(r"^ADDRESS\s*=\s*(0x[0-9A-Fa-f]+)", (SPECS / f"{name}.py").read_text(), re.M)
        if match:
            found.add(int(match.group(1), 16))
    return found


def known_wrong():
    text = (ROOT / "KNOWN_WRONG_LIFTS.md").read_text()
    return {int(a, 16) for a in re.findall(r"0x(82[0-9A-Fa-f]{6})", text)}


def status(address, ok, done, wrong):
    if address in wrong:
        return "wrong"
    if address in ok:
        return "verified"
    if address in done:
        return "lifted"
    return "todo"


def print_split(title, weights):
    total = sum(weights.values()) or 1
    print(title)
    for key in ORDER:
        print(f"  {key:9}{weights.get(key, 0):>12,.0f}  {100 * weights.get(key, 0) / total:5.1f}%")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path)
    parser.add_argument("--hot", type=Path)
    args = parser.parse_args()

    ok = verified(args.log.read_text() if args.log else None)
    done, wrong = lifted(), known_wrong()

    counts = {}
    for address in all_functions():
        key = status(address, ok, done, wrong)
        counts[key] = counts.get(key, 0) + 1
    print_split("All functions", counts)

    if args.hot:
        weighted, counted = {}, {}
        for line in args.hot.read_text().splitlines()[1:]:
            _, address, _, _, _, score, _ = line.split("\t")
            key = status(int(address, 16), ok, done, wrong)
            weighted[key] = weighted.get(key, 0) + float(score)
            counted[key] = counted.get(key, 0) + 1
        print_split("Functions a match runs", counted)
        print_split("Weighted by calls/s * size", weighted)


if __name__ == "__main__":
    main()
