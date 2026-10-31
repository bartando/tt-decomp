"""Mutations of the movement animation entry/reset path."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong suppression byte", "at<uint8_t>(state, 0x13) = 1", "at<uint8_t>(state, 0x13) = 0"),
    ("wrong locomotion mode", "->Start(0, nullptr, 0)", "->Start(1, nullptr, 0)"),
    ("leave phase running", "at<float>(phase, 0x19C) = 0.0f", "at<float>(phase, 0x19C) = 1.0f"),
    ("lose timing default", "at<float>(timing, 0x1C) = 1.0f", "at<float>(timing, 0x1C) = 0.0f"),
    ("leave global swing count", "g_swingCountFlag = 0", "g_swingCountFlag = 1"),
    ("cache timing before reset", "clearSwingTiming(at<void*>(state, 0x7C))", "clearSwingTiming(cachedTiming)"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_mode_animation.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, label
        mutated = source.replace(old, new)
        if label == "cache timing before reset":
            mutated = mutated.replace("    void* phase =", "    void* cachedTiming = at<void*>(state, 0x7C);\n    void* phase =")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_enter_movement_animation.py"),
                         Options(seed=1, trials=1000, patches=((source, mutated),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
