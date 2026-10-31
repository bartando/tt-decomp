"""Behavioral mutation checks for the full mode-animation reset."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("keep active slot", "at<void*>(state, 0x78) = nullptr", "at<void*>(state, 0x78) = state"),
    ("skip fifth record", "offset <= 0x74", "offset < 0x74"),
    ("omit record vector clear", "std::memset(static_cast<uint8_t*>(record) + 0x180, 0, 16)", "(void)record"),
    ("wrong carry multiplier", "0x5CDCFAA7u", "0x5CDCFAA9u"),
    ("drop RNG carry", " + g_prngState[1]", ""),
    ("truncate RNG sample", "& 0x7FFFFF", "& 0xFFFF"),
    ("wrong locomotion mode", "locomotion->Start(1, transform, 0)", "locomotion->Start(0, transform, 0)"),
    ("ignore skeleton flags", "at<uint32_t>(at<void*>(skeleton, 4), 0x14) & 1", "false"),
    ("reload live list count", "i < count", "i < at<uint16_t>(state, 0x4C)"),
    ("cache old entry array", "apply(at<uint32_t*>(state, 0x48)[i]", "apply(cachedEntries[i]"),
    ("wrong pair ID", "SetupAnimationPair(5, 6,", "SetupAnimationPair(5, 7,"),
    ("leave final mask byte", "slot * 14, 0, 14", "slot * 14, 0, 13"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_mode_animation.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, label
        mutated = source.replace(old, new)
        if label == "cache old entry array":
            mutated = mutated.replace("    const uint16_t count =", "    const uint32_t* cachedEntries = at<uint32_t*>(state, 0x48);\n    const uint16_t count =")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_reset_mode_animation.py"),
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
