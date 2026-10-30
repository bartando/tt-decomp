"""PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
tools/lift-check/specs/_cloth_collide_capsule_mutations.py

Compile broken copies in the build cache, leaving the checked-in lift intact.
Every mutation must report FAIL; BUILD/SPEC/UNSUPPORTED never count as caught.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("unrounded batch count", "lvlTable_7D28_2h(paddedCount, positions",
     "lvlTable_7D28_2h(particles.count, positions"),
    ("drop first-index suppression", "candidate > 0 && index == indices[0]", "false"),
    ("include radial equality", "inside &= radiusSq.lane[lane] > distanceSq;",
     "inside &= radiusSq.lane[lane] >= distanceSq;"),
    ("omit lower endcap clamp", "if (lowerTest > maskedProjection)", "if (false)"),
    ("unsigned movable comparison", "static_cast<int32_t>(index) < firstMovable",
     "index < static_cast<uint32_t>(firstMovable)"),
    ("add reduction instead of subtracting", "excess - flushVmx(shrink.lane[lane])",
     "excess + flushVmx(shrink.lane[lane])"),
    ("forget previous position", "const LvlTableVector origin = aligned(previous)[slot];",
     "const LvlTableVector origin{};"),
    ("discard response mode", "position, mode,\n                         direction, step, origin);",
     "position, 0,\n                         direction, step, origin);"),
    ("keep VMX subnormals", "        bits &= 0x80000000u;", "        /* missing VMX flush */"),
    ("truncate response loop", "                         direction, step, origin);",
     "                         direction, step, origin); // mutation\n        return;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/match/lvl_table.cpp").read_text()
    spec = Path(__file__).with_name("cloth_collide_capsule.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
