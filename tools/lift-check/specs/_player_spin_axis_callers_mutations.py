"""Ensure caller specs catch omitted float bounds and the camera-side byte."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_register_pad_slot", "discard camera-side byte", "metaByte, cameraSide);", "metaByte, 0);"),
    ("player_set_spin_axis", "missing unit bound", "pongPlayer_4EA0_g(sub, 0.0f, 1.0f);", "pongPlayer_4EA0_g(sub, 0.0f, 0.0f);"),
    ("player_accumulate_spin_axis", "discard caller maximum", "pongPlayer_4EA0_g(sub, 0.0f, maxLength);", "pongPlayer_4EA0_g(sub, 0.0f, 1.0f);"),
    ("player_accumulate_spin_axis", "lose accumulated width", "sub + 4) = oldWidth + widthDiff;", "sub + 4) = widthDiff;"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/game/player/pong_player.cpp").read_text()
    for spec, label, old, new in CASES:
        assert old in source, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
