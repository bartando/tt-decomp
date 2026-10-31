"""Require behavioral failures for fade curve selection and precision."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("swap curve selectors", "switch (fade->curve)", "switch (3 - fade->curve)"),
    ("omit log scale", "power * g_xactFadeLogScale", "power"),
    ("late float rounding", "const float power = static_cast<float>(std::pow(g_xactFadeLogBase, static_cast<double>(fade->progress)));",
     "const double power = std::pow(g_xactFadeLogBase, static_cast<double>(fade->progress));"),
    ("omit sine angle scaling", "static_cast<double>(fade->progress) * g_xactFadeHalfPi", "static_cast<double>(fade->progress)"),
    ("clamp linear curve", "fade->value = fade->progress;", "fade->value = fade->progress > 1.0f ? 1.0f : fade->progress;"),
]


def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("xact_fade_apply_curve.py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if caught else 'MISSED'} {label}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
