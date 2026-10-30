"""Run from the repo root with PYTHONPATH=tools/lift-check and the lift-check venv.

Mutations only touch build-cache copies. Only a behavioral FAIL counts as caught.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("count-only guard", "g_fxCountOnly == 0 || g_fxVertexCursor != 0", "g_fxCountOnly == 0 && g_fxVertexCursor != 0"),
    ("cursor stride", "g_fxVertexCursor += sizeof(FxBillboardVertex);\n        vertex->position[0] = x", "g_fxVertexCursor += 32;\n        vertex->position[0] = x"),
    ("x coordinate", "vertex->position[0] = x;", "vertex->position[0] = y;"),
    ("y coordinate", "vertex->position[1] = y;", "vertex->position[1] = x;"),
    ("depth", "vertex->position[2] = g_fxVertexDepth;", "vertex->position[2] = x;"),
    ("normal x", "vertex->normal[0] = g_fxVertexNormalX;", "vertex->normal[0] = g_fxVertexNormalY;"),
    ("normal y", "vertex->normal[1] = g_fxVertexNormalY;", "vertex->normal[1] = g_fxVertexNormalZ;"),
    ("normal z", "vertex->normal[2] = g_fxVertexNormalZ;", "vertex->normal[2] = g_fxVertexNormalX;"),
    ("colour", "vertex->color = g_fxCurrentColor;", "vertex->color = g_fxCurrentColor ^ 1;"),
    ("uv", "vertex->uv[0] = g_fxVertexU;", "vertex->uv[0] = g_fxVertexV;"),
    ("count", "++g_fxVertexCount;", "g_fxVertexCount += 2;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/graphics/fx_billboard.cpp").read_text()
    spec = Path(__file__).with_name("fx_emit_vertex_2d.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc == 1:
            caught += 1
        else:
            print(output.getvalue())
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return int(caught != len(MUTATIONS))


if __name__ == "__main__":
    raise SystemExit(main())
