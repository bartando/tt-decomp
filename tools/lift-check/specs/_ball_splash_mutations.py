import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("skip second record", "i < 2", "i < 1"),
    ("wrong stride", "i * 0x50", "i * 0x40"),
    ("wrong upper bound", "= 1000.0f", "= -1000.0f"),
    ("overwrite byte padding", "record[0] = 0;", "*reinterpret_cast<uint32_t*>(record) = 0;"),
    ("lose scalar reset", "0x44u, 0x48u", "0x44u"),
]

def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ball_splash_reset.py"),
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
