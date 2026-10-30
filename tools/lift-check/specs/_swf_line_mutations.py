"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_swf_line_mutations.py

Mutate build-cache copies only. Each case must produce a behavioral FAIL;
BUILD, SPEC and UNSUPPORTED do not count. The checked-in lifts stay intact.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


COMMON = (
    ("twip conversion", "const float sx = x * g_swfTwipsToPixels;", "const float sx = x;"),
    ("UV translation", "+ uv[4];", "+ uv[5];"),
    ("missing V update", "g_fxVertexV = std::fma(uv[3], sy, vProduct) + uv[5];", ""),
    ("pixel scale", "* g_swfPixelScaleX;", "* g_swfPixelScaleY;"),
    ("emitted coordinate order", "fxEmitVertex2D(screenX, screenY);", "fxEmitVertex2D(screenY, screenX);"),
)
MUTATIONS = {
    "swf_emit_line_vertex_offset_x": ("swfEmitLineVertexOffsetX", COMMON + (
        ("offset sign", "std::fma(offset, g_swfTwipsToPixels, sx)", "std::fma(-offset, g_swfTwipsToPixels, sx)"),
        ("offset axis", "m[0] * shiftedX", "m[0] * sy"),
        ("offset leaks into UV", "uv[0] * sx", "uv[0] * shiftedX"),
        ("unfused position", "std::fma(m[3], sy, yProduct)", "(m[3] * sy + yProduct)"),
    )),
    "swf_emit_line_vertex_offset_y": ("swfEmitLineVertexOffsetY", COMMON + (
        ("offset sign", "std::fma(offset, g_swfTwipsToPixels, sy)", "std::fma(-offset, g_swfTwipsToPixels, sy)"),
        ("offset axis", "std::fma(m[3], shiftedY, yProduct)", "std::fma(m[3], sx, yProduct)"),
        ("offset leaks into UV", "std::fma(uv[2], sy, uProduct)", "std::fma(uv[2], shiftedY, uProduct)"),
        ("unfused position", "std::fma(m[3], shiftedY, yProduct)", "(m[3] * shiftedY + yProduct)"),
    )),
    "swf_draw_line": ("swfDrawLine", (
        ("primitive type", "rage_2A78(5, 6);", "rage_2A78(4, 6);"),
        ("vertex count", "rage_2A78(5, 6);", "rage_2A78(5, 5);"),
        ("half width", "width * 0.5f", "width * 0.25f"),
        ("remaining width", "width - halfWidth", "width + halfWidth"),
        ("equal-axis branch", "if (absX > absY)", "if (absX >= absY)"),
        ("unordered axis branch", "if (absX > absY)", "if (!(absX <= absY))"),
        ("first vertex axis", "swfEmitLineVertexOffsetY(x0, y0, -halfWidth);", "swfEmitLineVertexOffsetX(x0, y0, -halfWidth);"),
        ("X end-cap direction", "x1 > x0 ? remainingWidth : -remainingWidth", "x1 > x0 ? -remainingWidth : remainingWidth"),
        ("X start-cap direction", "x0 < x1 ? -halfWidth : halfWidth", "x0 < x1 ? halfWidth : -halfWidth"),
        ("unordered Y start cap", "y0 < y1 ? -halfWidth : halfWidth", "!(y0 >= y1) ? -halfWidth : halfWidth"),
        ("Y end-cap direction", "y1 > y0 ? remainingWidth : -remainingWidth", "y1 > y0 ? -remainingWidth : remainingWidth"),
        ("missing final vertex", "swfEmitLineVertexOffsetX(x1, y1, -halfWidth);", ""),
        ("device completion", "device[0] = device[13652 / 4];", ""),
        ("cursor cleanup", "g_fxVertexCursor = 0;", ""),
        ("count-only cleanup", "g_fxCountOnly = 0;", "g_fxCountOnly = 1;"),
    )),
}


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/swf.cpp").read_text()
    total = 0
    for spec_name, (function, cases) in MUTATIONS.items():
        start = source.index(f"void {function}(")
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for name, old, new in cases:
            # Count-only cleanup intentionally has one assignment per branch.
            assert body.count(old) == (2 if name == "count-only cleanup" else 1), name
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(trials=1000, seed=1,
                                     patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}/{name}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
        print(f"Caught {len(cases)}/{len(cases)} mutations for {spec_name}", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
