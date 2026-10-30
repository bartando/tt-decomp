"""Run from the repository root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ph_level_query_overlaps_node_mutations.py

Mutate build-cache copies only; the real source stays intact. Only behavioral
FAIL (exit 1) counts as caught, never BUILD/SPEC/UNSUPPORTED.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = [
    ("sphere omits node padding",
     "case 0: { // Sphere: circumscribed sphere, then expanded cube; tangencies excluded.\n"
     "        const float extent = node->halfWidth + node->padding;",
     "case 0: { // Sphere: circumscribed sphere, then expanded cube; tangencies excluded.\n"
     "        const float extent = node->halfWidth;"),
    ("sphere skips circumscribed rejection", "if (dot3(offset) >= broadRadius * broadRadius) {",
     "if (false) {"),
    ("sphere includes face tangency", "return fabsf(offset[0]) < axisRadius &&",
     "return fabsf(offset[0]) <= axisRadius &&"),
    ("segment admits boundary-only contact",
     "if (lower >= node->centre[axis] + extent || upper <= node->centre[axis] - extent)",
     "if (lower > node->centre[axis] + extent || upper < node->centre[axis] - extent)"),
    ("segment drops yz separating axis", "if (fabsf(yz) > (fabsf(direction[1]) + fabsf(direction[2])) * extent)",
     "if (false)"),
    ("segment drops zx separating axis", "if (fabsf(zx) > (fabsf(direction[0]) + fabsf(direction[2])) * extent)",
     "if (false)"),
    ("segment drops xy separating axis",
     "return !(fabsf(xy) > (fabsf(direction[0]) + fabsf(direction[1])) * extent);",
     "return 1;"),
    ("cylinder skips circumscribed rejection",
     "if (__builtin_fmaf(dz, dz, dxSq) >= broadRadius * broadRadius) {", "if (false) {"),
    ("cylinder includes y",
     "const float dx = node->centre[0] - query->start[0];",
     "const float dx = node->centre[1] - query->start[1];"),
    ("capsule endpoint omits length",
     "flush(query->endOrRadius[axis]) * flush(query->length)",
     "flush(query->endOrRadius[axis])"),
    ("capsule omits radius", "halfExtents.xyz[axis] = halfWidth + query->radius;",
     "halfExtents.xyz[axis] = halfWidth;"),
    ("capsule skips min/max rounding",
     "const float centre = flush(flush(flush(upper) + flush(lower)) * 0.5f);",
     "const float centre = node->centre[axis];"),
    ("point includes lower face",
     "if (node->centre[axis] - node->halfWidth >= query->start[axis] ||",
     "if (node->centre[axis] - node->halfWidth > query->start[axis] ||"),
    ("point excludes upper face",
     "node->centre[axis] + node->halfWidth < query->start[axis])",
     "node->centre[axis] + node->halfWidth <= query->start[axis])"),
    ("unknown type rejects", "return 1; // Unknown query types do not read the node.",
     "return 0; // Unknown query types do not read the node."),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/physics/ph_physics.cpp").read_text()
    spec = Path(__file__).with_name("ph_level_query_overlaps_node.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
