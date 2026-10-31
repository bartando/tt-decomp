import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("wrong mode two", "8.0f / 7.0f", "4.0f / 3.0f"),
    ("wrong widescreen", "16.0f / 9.0f", "4.0f / 3.0f"),
    ("omit stretch", "return state->stretch * factor;", "return factor;"),
    ("suppress zero-dimension NaN", "factor = dimension / dimension;", "factor = 1.0f;"),
    ("wrong mode range", "if (mode < 4)", "if (mode < 3)"),
]

def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("camera_display_aspect.py"),
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
