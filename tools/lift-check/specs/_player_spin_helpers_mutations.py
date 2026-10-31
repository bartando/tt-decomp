"""Require behavioral FAIL for deliberately broken spin helper lifts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/player/player_spin_helpers.cpp"
CASES = [
    ("player_select_spin_magnitude", [
        ("lose special override", "if (special) row = 0x34;", "if (special) row = 0x10;"),
        ("wrong third direction", "direction == 3 ? 2 : direction", "direction == 3 ? 1 : direction"),
        ("ignore shot type eight", "shotType == 9 || shotType == 8", "shotType == 9"),
        ("wrong unknown-direction default", "if (direction > 3) return at<float>(settings, 0x10);", "if (direction > 3) return at<float>(settings, 0x14);"),
    ]),
    ("player_orient_spin_to_shot", [
        ("reverse side orientation", "positiveSide = source.lane[2] > 0.0f", "positiveSide = source.lane[2] < 0.0f"),
        ("omit flight normalization", "direction = normalize3(delta)", "direction = delta"),
        ("lose vertical spin", "output.lane[1] = verticalSpin;", "output.lane[1] = 0.0f;"),
        ("lose side query", "phBoundCapsule_DD20_fw(dot3(tableDirection, direction));", "phBoundCapsule_DD20_fw(0.0f);"),
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
