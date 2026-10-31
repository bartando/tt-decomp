"""Intentional breakages of the inner-creature mode transition lift."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("lose same-mode activation", "!at<uint8_t>(state, 0x14) && mode == 7", "false"),
    ("wrong locomotion start mode", "->Start(1, nullptr, 0)", "->Start(0, nullptr, 0)"),
    ("omit exit-seven signal", "g_selectionKillSignal[1] == 0", "true"),
    ("omit velocity clamp", "clampVelocity(at<float>(mover, 0x30), speed)", "at<float>(mover, 0x30)"),
    ("drop fourth matrix row", "transform, 64", "transform, 48"),
    ("ignore poll low byte", "static_cast<uint8_t>(io_Input_poll_9D68(settings))", "io_Input_poll_9D68(settings)"),
    ("wrong transition mask", "0x80 | (bit & 0x7F)", "bit"),
    ("clear idle commit flags", "mode != 7 && mode != 0", "mode != 7"),
    ("lose final mode", "at<int32_t>(creature, 0xC8) = mode;", "at<int32_t>(creature, 0xC8) = 0;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/creature_move_mode.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("creature_set_move_mode.py"),
                         Options(seed=1, trials=1000,
                                 patches=((source, source.replace(old, new)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
