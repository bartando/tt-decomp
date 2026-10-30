"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python
    tools/lift-check/specs/_rage_vector30_add_scaled_mutations.py

Patches apply only to checker build copies; only behavioral failures count.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("skip last component", "i < 30", "i < 29"),
    ("wrong source component", "source[i], weight", "source[(i + 1) % 30], weight"),
    ("subtract source", "source[i], weight", "source[i], -weight"),
    ("discard destination", "weight, destination[i]", "weight, 0.0f"),
    ("round product before addition", "destination[i] = __builtin_fmaf(source[i], weight, destination[i]);",
     "volatile float product = source[i] * weight;\n        destination[i] = product + destination[i];"),
    ("snapshot source", "for (unsigned i = 0; i < 30; ++i) {",
     "float copy[30];\n    for (unsigned i = 0; i < 30; ++i) copy[i] = source[i];\n"
     "    source = copy;\n    for (unsigned i = 0; i < 30; ++i) {"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/math/rage_math.cpp").read_text()
    spec = Path(__file__).with_name("rage_vector30_add_scaled.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
