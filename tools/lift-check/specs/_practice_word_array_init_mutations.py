import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("wrong allocation size", "unsignedCapacity * 4u", "unsignedCapacity * 8u"),
    ("lose size saturation", "? UINT32_MAX :", "? 0u :"),
    ("wrong count", "array->m_count = capacity;", "array->m_count = 0;"),
    ("lose flags", "array->m_flags & 0x3Fu", "0u"),
    ("wrong flag bit", "uint32_t(flag6) << 6", "uint32_t(flag6) << 7"),
    ("omit fill", "static_cast<uint32_t>(i);", "0u;"),
    ("omit shuffle", "gmPracticeTargetWordArray_Shuffle(array);", "/* shuffle lost */"),
]

def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("match_practice_word_array_init.py"),
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
