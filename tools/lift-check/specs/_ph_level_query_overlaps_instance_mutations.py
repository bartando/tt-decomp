"""From repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ph_level_query_overlaps_instance_mutations.py

Patches only build-cache copies. Each mutation must produce a behavioral FAIL;
BUILD/SPEC/UNSUPPORTED errors do not count as detection.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = [
    ("either mask instead of both", "& query->typeMask) == 0 ||",
     "& query->typeMask) == 0 &&"),
    ("swapped mask", "& query->typeMask)", "& query->includeMask)"),
    ("unknown type rejection", "return 1; // Unknown query types", "return 0; // Unknown query types"),
    ("wrong transform matrix", "reinterpret_cast<const float*>(inst + 0x10), centre",
     "reinterpret_cast<const float*>(inst + 0x20), centre"),
    ("sphere tangency", "return dot3(offset, offset) < radius * radius;",
     "return dot3(offset, offset) <= radius * radius;"),
    ("segment start tangency", "return dot3(offset, offset) <= radiusSq;",
     "return dot3(offset, offset) < radiusSq;"),
    ("segment interior area", "lengthSq, -projectionSq)", "lengthSq, projectionSq)"),
    ("cylinder includes Y", "const float dxSq = dx * dx;",
     "const float dy = query->start[1] - centre[1];\n        const float dxSq = dx * dx + dy * dy;"),
    ("capsule end clamp", "along = query->length;", "along = 0.0f;"),
    ("capsule omits bound radius", "const float radius = query->radius + boundRadius;",
     "const float radius = query->radius;"),
    ("point uses query radius", "return dot3(offset, offset) < boundRadius * boundRadius;",
     "return dot3(offset, offset) < query->endOrRadius[0] * query->endOrRadius[0];"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/physics/ph_physics.cpp").read_text()
    start = source.index("uint8_t phLevelNew_QueryOverlapsInstance(")
    body = source[start:source.index("\n}", start) + 2]
    spec = Path(__file__).with_name("ph_level_query_overlaps_instance.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert body.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((body, body.replace(old, new)),))).run()
        report = output.getvalue()
        detected = rc == 1 and "FAIL" in report
        first = report.splitlines()[0]
        print(f"{'CAUGHT' if detected else 'MISSED'} {name}: {first}", flush=True)
        if not detected:
            print(report)
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
