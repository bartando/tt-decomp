import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("wrong destination", "context + 0x40", "context + 0x30"),
    ("wrong enabled flag", "context[0x105]", "context[0x104]"),
    ("forget relock", "context[0x104] = 0;", "context[0x104] = 1;"),
    ("forget unlock", "context[0x104] = 1;", "context[0x104] = 0;"),
    ("omit disabled warning", 'nop_8240E6D0("Cannot Lock when Unlock is not enabled");', '/* warning lost */'),
]

def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ball_prediction_copy_locked.py"),
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
