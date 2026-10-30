"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
tools/lift-check/specs/_cloth_collide_edges_mutations.py

Only behavioral FAILs count. Mutations affect cached build copies, never the
working source; BUILD/SPEC/UNSUPPORTED results fail this mutation check.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("wrong composite dispatch", "composite->type != 9", "composite->type != 12"),
    ("floor triplet count", "(static_cast<uint32_t>(self->rangeWordCount) + 2) / 3",
     "static_cast<uint32_t>(self->rangeWordCount) / 3"),
    ("skip last range", "range < rangeCount", "range + 1 < rangeCount"),
    ("unsigned edge range", "if (first >= end)",
     "if (static_cast<uint32_t>(first) >= static_cast<uint32_t>(end))"),
    ("bypass edge indirection", "const uint32_t edgeIndex = self->edgeIndices[indexSlot];",
     "const uint32_t edgeIndex = cursor & 7u;"),
    ("truncate edge loop", "while (--remaining != 0)", "while (--remaining > 1)"),
    ("discard margin", "const float margin = self->margin;", "const float margin = 0.0f;"),
    ("lose parallel fallback", "const bool parallel = flushVmx(threshold)", "const bool parallel = false && flushVmx(threshold)"),
    ("omit lower edge clamp", "if (flushVmx(threshold) > flushVmx(maskLane(edgeParameter, mask)))",
     "if (false)"),
    ("omit upper edge clamp", "if (!(flushVmx(threshold) > flushVmx(upperTest)))", "if (false)"),
    ("clamp capsule axis", "mul(axis.lane[lane], axisParameter)",
     "mul(axis.lane[lane], axisParameter < 0.0f ? 0.0f : (axisParameter > 1.0f ? 1.0f : axisParameter))"),
    ("taper at closest point", "dot3(direction, clothSubtract(midpoint, start))",
     "dot3(direction, clothSubtract(onEdge, start))"),
    ("discard taper slope", "mul(slope.lane[lane], projection)", "0.0f"),
    ("include w in dot", "return flushVmx(dot(a, b, 3));", "return flushVmx(dot(a, b, 4));"),
    ("omit tiny-normal cutoff", "const float direction = small ? zero :", "const float direction = false ? zero :"),
    ("pull instead of push", "mul(direction, penetration)", "mul(-direction, penetration)"),
    ("skip second endpoint", "secondPosition->lane[lane] = add(second.lane[lane], correction.lane[lane]);",
     "secondPosition->lane[lane] = second.lane[lane];"),
    ("overwrite second with first", "add(second.lane[lane], correction.lane[lane])",
     "add(point.lane[lane], correction.lane[lane])"),
    ("keep VMX subnormals", "        bits &= 0x80000000u;", "        /* missing VMX flush */"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/match/lvl_table.cpp").read_text()
    start = source.index("// @ 0x82338D28 |")
    end = source.index("// @ 0x82340900 |", start)
    function = source[start:end]
    spec = Path(__file__).with_name("cloth_collide_edges.py")
    caught = 0
    for name, old, new in MUTATIONS:
        if old in function:
            assert function.count(old) == 1, f"mutation anchor changed: {name}"
            patch = (function, function.replace(old, new))
        else:
            assert source.count(old) == 1, f"mutation anchor changed: {name}"
            patch = (old, new)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=240, seed=1, patches=(patch,))).run()
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
