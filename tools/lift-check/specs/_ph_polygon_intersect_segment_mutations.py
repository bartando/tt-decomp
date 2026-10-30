"""Run from the repo root with PYTHONPATH=tools/lift-check and the lift-check venv.

Only behavioral FAIL counts; the patches affect build-cache copies, not the source.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("skip second triangle", "result >= 4 && indices[3] != 0", "result > 4 && indices[3] != 0"),
    ("test triangle on any miss", "result >= 4 && indices[3] != 0", "result >= 1 && indices[3] != 0"),
    ("wrong second triangle vertex", "vertices + 4 * indices[3], &startDistance", "vertices + 4 * indices[1], &startDistance"),
    ("reject equality", "fraction > maxFraction", "fraction >= maxFraction"),
    ("wrong hit point", "point[i] = product + segment[i]", "point[i] = product - segment[i]"),
    ("wrong distance sign", "= -endDistance;", "= endDistance;"),
    ("wrong hit type", "out + 66) = 2;", "out + 66) = 3;"),
    ("omit hit flag", "out[68] = 1;", "out[68] = 0;"),
    ("return false for hit", "    return 1;\n}\n\n// Sphere contact", "    return 0;\n}\n\n// Sphere contact"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/physics/ph_physics.cpp").read_text()
    spec = Path(__file__).with_name("ph_polygon_intersect_segment.py")
    caught = 0
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
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
