"""Patch cache copies only; every mutation must produce behavioral FAIL (1).

Run: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_swf_color_transform_mutations.py
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = (
    ("empty lift", "    int32_t factors[4];", "    return;\n    int32_t factors[4];"),
    ("unsigned inherited multiplier", "static_cast<int8_t>(parent[channel])", "parent[channel]"),
    ("unsigned local offset", "static_cast<int8_t>(local[channel + 4])", "local[channel + 4]"),
    ("divide negative product toward zero", "(static_cast<int8_t>(local[channel + 4]) * inherited) >> 6", "(static_cast<int8_t>(local[channel + 4]) * inherited) / 64"),
    ("lose signed byte wrap", "static_cast<int8_t>((static_cast<int8_t>(local[channel]) * inherited) >> 6)", "((static_cast<int8_t>(local[channel]) * inherited) >> 6)"),
    ("omit inherited offset", "offset + parent[channel + 4]", "offset"),
    ("wrong tint divisor", "/ 255", "/ 256"),
    ("swap red/green tint", "(rgb >> 16)", "(rgb >> 8)"),
    ("include upper alpha bits", "int32_t(alpha & 255)", "int32_t(alpha & 65535)"),
    ("reverse offset writes breaks overlap", "unsigned channel = 0; channel < 4; ++channel", "unsigned channel = 4; channel-- > 0;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/swf.cpp").read_text()
    start = source.index("void swfConcatColorTransform(")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    for label, old, new in CASES:
        assert body.count(old) == (4 if label == "wrong tint divisor" else 1), label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("swf_concat_color_transform.py"),
                         Options(seed=1, patches=((body, body.replace(old, new)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} SWF color mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
