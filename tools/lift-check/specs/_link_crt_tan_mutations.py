"""Reject broken tangent arithmetic and exceptional/zero handling."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong reciprocal sign", "denominator / -numerator", "denominator / numerator"),
    ("wrong reduction scale", "x * 0x1.45f306dc9c883p-1", "x * 0x1.0p0"),
    ("lose zero return", "return x;", "return 1.0;"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/math/ph_math.cpp").read_text()
    start = source.index("double crt_tan(double x)")
    end = source.index("\n}", start) + 2
    body = source[start:end]
    for label, old, new in MUTATIONS:
        assert old in body, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("link_crt_tan.py"),
                         Options(seed=1, patches=((body, body.replace(old, new)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
