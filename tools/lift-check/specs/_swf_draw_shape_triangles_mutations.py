"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_swf_draw_shape_triangles_mutations.py

Mutate build-cache copies only. Require a passing baseline and behavioral FAIL
(exit 1) for every mutation; BUILD/SPEC/UNSUPPORTED never count as detection.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("primitive type", "rage_2A78(3,", "rage_2A78(5,"),
    ("vertex count", "static_cast<int32_t>(count));", "static_cast<int32_t>(count) + 1);"),
    ("command coordinate stride", "words + 1 + 2 * i", "words + 1 + i"),
    ("solid instead of gradient", "fill->gradient ?", "false ?"),
    ("gradient receives scaled coordinates", "swfSampleGradient(fill->gradient, x, y)",
     "swfSampleGradient(fill->gradient, x * g_swfTwipScale, y * g_swfTwipScale)"),
    ("unsigned colour multiplier", "* multiply[channel]", "* uint8_t(multiply[channel])"),
    ("truncate negative colour product", "((int((color >> shift) & 255) * multiply[channel]) >> 6)",
     "((int((color >> shift) & 255) * multiply[channel]) / 64)"),
    ("colour addition scale", "int(add[channel]) * 4", "int(add[channel])"),
    ("omit upper colour clamp", "value > 255 ? 255 : value", "value"),
    ("alpha divisor", "value * state[71] / 255", "value * state[71] / 256"),
    ("omit twip conversion", "const float px = x * g_swfTwipScale;", "const float px = x;"),
    ("world matrix coefficient", "std::fma(world[2], py,", "std::fma(world[3], py,"),
    ("unfused world transform", "std::fma(world[2], py, world[0] * px)",
     "(world[2] * py + world[0] * px)"),
    ("pixel scale axis", "+ world[4]) * g_swfPixelScaleX", "+ world[4]) * g_swfPixelScaleY"),
    ("UV translation", "+ fill->textureMatrix[4];", "+ fill->textureMatrix[5];"),
    ("omit emitted vertex", "fxEmitVertex2D(screenX, screenY);", ""),
    ("device completion", "        device[0] = device[13652 / 4];", ""),
    ("cursor cleanup", "        g_fxVertexCursor = 0;", ""),
    ("count-only cleanup", "    g_fxCountOnly = 0;", ""),
    ("consumed command words", "return count * 2u + 1u;", "return count * 2u;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/swf.cpp").read_text()
    spec = Path(__file__).with_name("swf_draw_shape_triangles.py")
    if Checker(spec, Options(trials=100, seed=1)).run() != 0:
        return 1
    start = source.index("uint32_t swfDrawShapeTriangles(")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    for name, old, new in MUTATIONS:
        assert body.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1,
                                      patches=((body, body.replace(old, new, 1)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
