"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python <this file>.

Mutate build-cache copies only. Each deliberate breakage must return behavioral
FAIL (1); BUILD, SPEC, UNSUPPORTED and passing mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

COLOR = (
    ("skip store", "    *out = (alpha << 24) | (red << 16) | (green << 8) | blue;", "    (void)out;"),
    ("swap red and blue", "(red << 16) | (green << 8) | blue", "(blue << 16) | (green << 8) | red"),
    ("lose alpha", "(alpha << 24)", "0u"),
    ("wrong green shift", "(green << 8)", "(green << 4)"),
    ("wrong scale", "const float scale = g_alphaMultiplier;", "const float scale = g_alphaMultiplier - 1.0f;"),
    ("round instead of truncate", "static_cast<int32_t>(r * scale)", "static_cast<int32_t>(r * scale + 0.5f)"),
    ("skip lower clamp", "!(color->x >= low) ? low", "!(color->x >= low) ? -high"),
    ("skip upper clamp", "color->y <= high ? color->y : high", "color->y <= high ? color->y : low"),
    ("NaNs map to white", "!(color->z >= low) ? low", "!(color->z >= low) ? high"),
    ("write before snapshot breaks overlap", "    const float r =", "    *out = 0;\n    const float r ="),
    ("wrong output word", "    *out =", "    out[1] ="),
    ("wrong return pointer", "    return out;", "    return out + 1;"),
)
GETTER = (
    ("wrong field offset", "+ 16", "+ 12"),
    ("return object", "+ 16", "+ 0"),
    ("dereference instead of address", "return reinterpret_cast<float*>(reinterpret_cast<uint8_t*>(this) + 16);", "return *reinterpret_cast<float**>(reinterpret_cast<uint8_t*>(this) + 16);"),
    ("unexpected initialization", "    return", "    *reinterpret_cast<uint8_t*>(this) = 0;\n    return"),
    ("mask pointer alignment", "return reinterpret_cast<float*>(reinterpret_cast<uint8_t*>(this) + 16);", "return reinterpret_cast<float*>((reinterpret_cast<uintptr_t>(this) + 16) & ~uintptr_t(15));"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, path, signature, cases in (
        ("pack_clamped_color_argb8", "src/graphics/fx_effects.cpp", "uint32_t* PackClampedColorARGB8(", COLOR),
        ("cr_anim_dof_vector3_get_vector", "src/rage/animation/rage_anim.cpp", "float* crAnimDofVector3::GetVector()", GETTER),
    ):
        source = (root / path).read_text()
        start = source.index(signature)
        end = source.index("\n}", start) + 2
        body = source[start:end]
        for label, old, new in cases:
            assert body.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((body, body.replace(old, new, 1)),))).run()
            lines = output.getvalue().splitlines()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {lines[0] if lines else '(no output)'}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} color/getter mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
