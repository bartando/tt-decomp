"""Require behavioral mismatches for rounding, branch and field mutations."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("float_approach", "wrong upward sign", "current = __builtin_fmaf(rate, deltaTime, current);", "current = __builtin_fmaf(-rate, deltaTime, current);"),
    ("float_approach", "wrong downward sign", "current = -__builtin_fmaf(rate, deltaTime, -current);", "current = __builtin_fmaf(rate, deltaTime, current);"),
    ("float_approach", "lose upward clamp", "if (current > target) *value = target;", "/* clamp lost */"),
    ("float_approach", "lose downward clamp", "if (current < target) *value = target;", "/* clamp lost */"),
    ("float_approach", "unordered NaN branch", "if (current < target) {", "if (!(current >= target)) {"),
    ("float_approach", "wrong completion", "return *value == target;", "return *value != target;"),
    ("ph_float_property", "wrong field", "+ 0x48", "+ 0x44"),
]

def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        ok = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if ok else 'MISSED'} {label}: {first}", flush=True)
        if not ok:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
