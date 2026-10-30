"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python <this file>."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("inactive returns one", "fade->state != 2) return 0;", "fade->state != 2) return 1;"),
    ("wrong duration", "static_cast<float>(fade->duration)", "static_cast<float>(fade->duration + 1)"),
    ("up subtracts", "fade->progress += step;", "fade->progress -= step;"),
    ("down adds", "fade->progress -= step;", "fade->progress += step;"),
    ("up callback slot", "fade->vtable[1]", "fade->vtable[0]"),
    ("down callback slot", "fade->vtable[0]", "fade->vtable[1]"),
    ("retain state", "fade->state = 0;", "fade->state = 3;"),
    ("wrong upper bound", "fade->value = g_xactFadeOne;", "fade->value = g_xactFadeZero;"),
    ("wrong lower bound", "fade->value = g_xactFadeZero;", "fade->value = g_xactFadeOne;"),
]

def main():
    spec = Path(__file__).with_name("xact_fade_update.py")
    for name, old, new in MUTATIONS:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {out.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(out.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
