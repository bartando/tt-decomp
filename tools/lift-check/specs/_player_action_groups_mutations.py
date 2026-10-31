"""Reject behavior changes to the action-group propagation lift."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong mode-seven weight", "== 7 ? 0.0f : 0.75f", "== 7 ? 0.75f : 0.75f"),
    ("write skipped groups", "if (at<uint8_t>(group, 0x3D)) continue;", "if (false) continue;"),
    ("lose enable byte", "at<uint8_t>(group, 0x34) = enable;", "at<uint8_t>(group, 0x34) = 0;"),
    ("reset disabled children", " || !enable", ""),
    ("reset running children", " || at<float>(group, 0x30) != 0.0f", ""),
    ("cache group count", "i < at<uint16_t>(player, 0x1818)", "i < count"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_action_groups.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, label
        mutated = source.replace(old, new)
        if label == "cache group count":
            mutated = mutated.replace("    for (uint32_t i", "    const uint32_t count = at<uint16_t>(player, 0x1818);\n    for (uint32_t i")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_enable_action_groups.py"),
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
