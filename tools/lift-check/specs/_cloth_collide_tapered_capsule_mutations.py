"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
tools/lift-check/specs/_cloth_collide_tapered_capsule_mutations.py

Compile deliberately broken copies in the build cache. Only behavioral FAILs
count as caught; BUILD, SPEC and UNSUPPORTED are errors, not successful tests.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("unrounded batch count", "lvlTable_7D28_2h(batchCount, positions",
     "lvlTable_7D28_2h(particles.count, positions"),
    ("drop first-index suppression", "cursor > 0 && index == indices[0]", "false"),
    ("include radial equality", "> flushVmx(maskLane(distanceSq, lbl_82619BE0[lane]));",
     ">= flushVmx(maskLane(distanceSq, lbl_82619BE0[lane]));"),
    ("omit lower endcap", "const bool belowLower = zero > lowerOffset;", "const bool belowLower = false;"),
    ("omit upper endcap clamp", "belowUpper ? projection : upperProjection.lane[lane]", "projection"),
    ("discard varying radius", "belowUpper ? taperedRadius : upperRadius.lane[lane]", "upperRadius.lane[lane]"),
    ("include w radius in overlap", "maskLane(radiusSq, lbl_82619BE0[lane], lbl_82619BD0[lane])", "radiusSq"),
    ("swap packed radius and scale", "distanceSq, normalScale.lane[0], radius.lane[0], normalSlope.lane[0]",
     "distanceSq, radius.lane[0], normalScale.lane[0], normalSlope.lane[0]"),
    ("lose axial normal component", "const float axial = flushVmx(flushVmx(packed.lane[3]) * length);",
     "const float axial = 0.0f;"),
    ("unsigned movable comparison", "static_cast<int32_t>(index) < movableStart",
     "index < static_cast<uint32_t>(movableStart)"),
    ("add reduction instead of subtracting", "excess - flushVmx(reductionValue.lane[lane])",
     "excess + flushVmx(reductionValue.lane[lane])"),
    ("forget previous position", "const LvlTableVector previousPosition = aligned(previous)[slot];",
     "const LvlTableVector previousPosition{};"),
    ("discard response mode", "mode, direction, step, previousPosition);", "0, direction, step, previousPosition);"),
    ("truncate response loop", "mode, direction, step, previousPosition);",
     "mode, direction, step, previousPosition);\n        return;"),
    ("keep VMX subnormals", "        bits &= 0x80000000u;", "        /* missing VMX flush */"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/match/lvl_table.cpp").read_text()
    start = source.index("// @ 0x823389E8")
    end = source.index("// @ 0x823D85B8", start)
    function = source[start:end]
    spec = Path(__file__).with_name("cloth_collide_tapered_capsule.py")
    caught = 0
    for name, old, new in MUTATIONS:
        # Scope patches to this lift, even when a sibling shares an expression.
        if old in function:
            assert function.count(old) == 1, f"mutation anchor changed: {name}"
            patch = (function, function.replace(old, new))
        else:
            assert source.count(old) == 1, f"mutation anchor changed: {name}"
            patch = (old, new)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=(patch,))).run()
        first = output.getvalue().splitlines()[0]
        detected = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if detected else 'MISSED'} {name}: {first}", flush=True)
        if not detected:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
