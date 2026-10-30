"""Run with the lift-check venv and PYTHONPATH=tools/lift-check from the repo root.

Mutations are compiled in the build cache; the checked-in lift stays untouched.
Each must produce FAIL (a BUILD/SPEC error does not count as detection).
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/graphics/fx_billboard.cpp").read_text()
    source = source.replace('"fx_effects.hpp"', '"graphics/fx_effects.hpp"')
    spec = Path(__file__).with_name("fx_draw_billboard_quad.py")
    include = '#include "../../../src/graphics/fx_billboard.cpp"'
    mutations = [
        ("rotation mask", "phase) & 511", "phase) & 255"),
        ("UV pairing", "uv[corner < 2 ? 1 : 3]", "uv[corner < 2 ? 3 : 1]"),
        ("vertex stride", "g_fxVertexCursor += sizeof(FxBillboardVertex)",
         "g_fxVertexCursor += 32"),
        ("packed colour", "vertex->color = color", "vertex->color = color ^ 1"),
        ("count-only guard", "countOnly == 0 || g_fxVertexCursor != 0", "countOnly == 0"),
        ("vertex count", "g_fxVertexCount += 4", "g_fxVertexCount += 3"),
        ("corner arithmetic", "(u + r) + center[axis]", "u + (r + center[axis])"),
    ]
    for name, old, new in mutations:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        mutated = source.replace(old, new, 1)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((include, mutated),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}")
        if rc != 1:
            print(output.getvalue())
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
