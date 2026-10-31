"""Only behavioral FAIL counts as catching an intentionally broken lift."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("ignore special mode", "mode != 1 &&", "mode != 2 &&"),
    ("ignore pending cancellation", "at<uint8_t>(player, 0x18B8)\n", "false\n"),
    ("reset unchanged mode", "at<int32_t>(player, 0x1CC) != mode", "true"),
    ("omit action timer reset", "at<float>(action, 0x4E8) = 0.0f;", "at<float>(action, 0x4E8) = 1.0f;"),
    ("wrong renderer slot", "(slot + 0x81) * 4", "(slot + 0x80) * 4"),
    ("enable mode seven", " && mode != 7", ""),
    ("lose mode storage", "at<int32_t>(player, 0x1CC) = mode;", "at<int32_t>(player, 0x1CC) = 0;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_move_mode.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, f"missing mutation anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_set_move_mode.py"),
                         Options(seed=1, trials=128,
                                 patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
