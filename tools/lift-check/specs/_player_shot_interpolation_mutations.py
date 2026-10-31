"""Require behavioral FAIL for deliberately broken spin-axis lifts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_player_shot_interpolation_mutations.py
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/player/player_shot_interpolation.cpp"
CASES = [
    ("player_clamp_spin_axis_length", [
        ("ignore max bound", "bound = maxLength;", "bound = minLength;"),
        ("lose minimum clamp", "bound = minLength;", "bound = 0.0f;"),
        ("omit w scaling", "lane < 4", "lane < 3"),
        ("zero fallback loses min", "value[1] = minLength;", "value[1] = 0.0f;"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    count = 0
    for spec, mutations in CASES:
        for label, old, new in mutations:
            assert old in source, f"missing anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
