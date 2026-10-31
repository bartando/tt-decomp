"""Catch wrong mover, side flag and missing contact position arguments."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_init_movement_contact", "wrong alternate flag", "CalcInitMatrix(matrix, mover, 0)", "CalcInitMatrix(matrix, mover, 1)"),
    ("player_init_movement_contact", "wrong matrix position", "reinterpret_cast<vec3*>(matrix + 12)", "reinterpret_cast<vec3*>(matrix)"),
    ("player_init_movement_contact", "ignore slot gate", "settings[slot + 14] != 0", "settings[slot + 14] == 0"),
    ("player_reset_serve_position", "wrong hand flip", "handedness == 0", "handedness != 0"),
    ("player_reset_serve_position", "lose alternate flag", "mover->Reset(alternate);", "mover->Reset(false);"),
]


def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
