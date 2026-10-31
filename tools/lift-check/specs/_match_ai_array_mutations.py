import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("wrong pointer stride", "capacity * 4u", "capacity * 8u"),
    ("wrong saturation", "? UINT32_MAX :", "? 0u :"),
    ("wrong capacity", "static_cast<uint16_t>(capacity)", "static_cast<uint16_t>(capacity + 1u)"),
    ("overwrite count", "array->m_capacity =", "array->m_count ="),
]

def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("match_ai_array_allocate.py"),
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
