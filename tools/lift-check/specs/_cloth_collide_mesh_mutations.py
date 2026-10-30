"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python
 tools/lift-check/specs/_cloth_collide_mesh_mutations.py

Mutations compile only in lift-check's build cache. The working source remains
intact. Only differential FAIL (exit 1) counts; BUILD/SPEC/UNSUPPORTED do not.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("one-hop walk", (("int attempts = 8", "int attempts = 1"),)),
    ("include upper equality", ((
        "> flushVmx(maskLane(limit.lane[lane], lbl_82619BE0[lane]));",
        ">= flushVmx(maskLane(limit.lane[lane], lbl_82619BE0[lane]));"),)),
    ("raise lower cutoff to zero", (("!above && !(distance >= -0.05f)", "!above && !(distance >= 0.0f)"),)),
    ("exclude lower equality", (("!above && !(distance >= -0.05f)", "!above && !(distance > -0.05f)"),)),
    ("use conventional cross product", ((
        "result.lane[lane] = flushVmx(-flushVmx(second - first));",
        "result.lane[lane] = flushVmx(-flushVmx(first - second));"),)),
    ("change edge tie choice", (("edge0 > edge2 ?", "edge0 >= edge2 ?"),)),
    ("guard on neighbour adjacency", ((
        "above && current->neighbours[nextEdge] == currentIndex",
        "above && contact->neighbours[nextEdge] == currentIndex"),)),
    ("use neighbour distance for response", ((
        "const float distance = clothFaceDistance(current, vertices, position);",
        "float distance = clothFaceDistance(current, vertices, position);"), (
        "const float nextDistance = clothFaceDistance(contact, vertices, position);",
        "const float nextDistance = clothFaceDistance(contact, vertices, position);\n"
        "                distance = nextDistance;"))),
    ("add reduction", ((
        "flushVmx(padding.lane[lane]) - flushVmx(shrink.lane[lane])",
        "flushVmx(padding.lane[lane]) + flushVmx(shrink.lane[lane])"),)),
    ("drop response mode", (("mode, normal, step, origin);", "0, normal, step, origin);"),)),
    ("drop previous position", ((
        "const LvlTableVector origin = loadClothVector(previous + particle);",
        "const LvlTableVector origin{};"),)),
    ("unsigned particle range", (("particle < end; ++particle",
        "static_cast<uint32_t>(particle) < static_cast<uint32_t>(end); ++particle"),)),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/match/lvl_table.cpp").read_text()
    spec = Path(__file__).with_name("cloth_collide_mesh.py")
    caught = 0
    for name, patches in MUTATIONS:
        for old, new in patches:
            assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=240, seed=1, patches=patches)).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
