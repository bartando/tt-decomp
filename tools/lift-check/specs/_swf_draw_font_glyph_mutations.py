"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_swf_draw_font_glyph_mutations.py

Patch build-cache copies only. Every mutation must produce a behavioral FAIL;
BUILD, SPEC and UNSUPPORTED do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("missing-texture guard", "if (!atlas->textures) return;", "if (atlas->textures) return;"),
    ("texture page selection", "atlas->textureIndices[glyphIndex]", "0"),
    ("cache-hit comparison", "g_swfGlyphRenderState.texture != texture", "g_swfGlyphRenderState.texture == texture"),
    ("cache write before bind", "        g_swfGlyphRenderState.texture = texture;", ""),
    ("primitive vertex count", "rage_2A78(4, 4);", "rage_2A78(4, 3);"),
    ("glyph index", "atlas->glyphs + glyphIndex", "atlas->glyphs"),
    ("quad corner order", "corner == 0 || corner == 2", "corner == 0 || corner == 1"),
    ("affine x coefficient", "std::fma(py, m[2], xProduct)", "std::fma(py, m[3], xProduct)"),
    ("fused multiply-add", "std::fma(py, m[2], xProduct)", "(py * m[2] + xProduct)"),
    ("UV sum", "glyph->u + glyph->width", "glyph->u - glyph->width"),
    ("final UV state", "            g_fxVertexU = u;", ""),
    ("count-only with cursor", "countOnly == 0 || g_fxVertexCursor != 0", "countOnly == 0"),
    ("vertex stride", "g_fxVertexCursor += sizeof(swfGlyphVertex);", "g_fxVertexCursor += 32;"),
    ("packed colour", "vertex->color = g_fxCurrentColor;", "vertex->color = g_fxCurrentColor ^ 1;"),
    ("vertex count", "g_fxVertexCount += 4;", "g_fxVertexCount += 3;"),
    ("device completion", "        device[0] = device[13652 / 4];", ""),
    ("cursor cleanup", "        g_fxVertexCursor = 0;", ""),
    ("count-only cleanup", "    g_fxCountOnly = 0;", ""),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/swf.cpp").read_text()
    spec = Path(__file__).with_name("swf_draw_font_glyph.py")
    include = '#include "../../../src/rage/swf.cpp"'
    start = source.index("void swfDrawFontGlyph(")
    end = source.index("\n}\n", start)
    body = source[start:end]
    caught = 0
    for name, old, new in MUTATIONS:
        assert body.count(old) == 1, f"mutation anchor changed: {name}"
        mutated = source[:start] + body.replace(old, new, 1) + source[end:]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1,
                                      patches=((include, mutated),))).run()
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
