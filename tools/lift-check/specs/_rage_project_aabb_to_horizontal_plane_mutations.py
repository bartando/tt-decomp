"""Run with PYTHONPATH=tools/lift-check and the lift-check venv from repo root.

Mutations patch build-cache copies only. A behavioral FAIL is required; build,
spec and unsupported-instruction errors do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("project empty boxes", "    if (!empty) {", "    if (true) {"),
    ("omit auxiliary center offset",
     "flushClipVmx(box[0][lane]) + flushClipVmx(box[2][lane])",
     "flushClipVmx(box[0][lane]) + 0.0f"),
    ("wrong viewpoint row",
     "flushClipVmx(corners[corner][axis]) -\n                                               flushClipVmx(camera[4][axis])",
     "flushClipVmx(corners[corner][axis]) -\n                                               flushClipVmx(camera[3][axis])"),
    ("wrong plane-height sign", "camera[4][1] - planeY", "camera[4][1] + planeY"),
    ("skip last projected corner", "corner < 8; ++corner) {\n            float direction[3]",
     "corner < 7; ++corner) {\n            float direction[3]"),
    ("omit ray normalization", "direction[axis] * inverseLength);",
     "direction[axis] * 1.0f);"),
    ("wrong lower clamp", "const float lowLimit = -limits[axis];",
     "const float lowLimit = limits[axis];"),
    ("accept zero-width footprint", "!(maximum[0] <= minimum[0]) && !(maximum[2] <= minimum[2])",
     "!(maximum[0] < minimum[0]) && !(maximum[2] < minimum[2])"),
    ("omit z rejection", "!(maximum[0] <= minimum[0]) && !(maximum[2] <= minimum[2])",
     "!(maximum[0] <= minimum[0])"),
    ("pad at threshold equality", "planeY < lbl_825C8078 ?", "planeY <= lbl_825C8078 ?"),
    ("omit footprint padding", "difference + flushClipVmx(padding[axis])", "difference + 0.0f"),
    ("wrong center divisor", "sum * (1.0f / lbl_8202D184)", "sum * (1.0f / 3.0f)"),
    ("omit active-camera clip", "            clipAabbToActiveCamera(context, output, nullptr);",
     "            /* mutated: omitted active-camera clip */"),
    ("leave rejection auxiliary dirty",
     "vector < 3; ++vector)\n        __builtin_memcpy(output[vector], lbl_82606740",
     "vector < 2; ++vector)\n        __builtin_memcpy(output[vector], lbl_82606740"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/math/polygon_clip.cpp").read_text()
    spec = Path(__file__).with_name("rage_project_aabb_to_horizontal_plane.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=300, seed=1, patches=((old, new),))).run()
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
