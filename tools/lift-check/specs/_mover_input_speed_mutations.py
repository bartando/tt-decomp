"""Behavioral mutation checks for the shared mover input-speed selection."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong forced-speed flag", "mover->m_flags & 4", "mover->m_flags & 2"),
    ("wrong settings stride", "slot * 36 + 0xC4", "slot * 4 + 0xC4"),
    ("only canonical active byte", "if (at<uint8_t>(settings, slot * 36 + 0xC4))", "if (at<uint8_t>(settings, slot * 36 + 0xC4) == 1)"),
    ("wrong forced-speed field", "0x14), 0x64)", "0x14), 0x58)"),
    ("omit character scaling", "return scale *", "return 1.0f *"),
    ("cache stale manager", "return scale * at<float>(at<void*>(g_gameDataMgr, 0x14), 0x58)", "return scale * cachedSpeed"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/creature/mover_input_speed.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, label
        mutated = source.replace(old, new)
        if label == "cache stale manager":
            mutated = mutated.replace("    void* character =", "    const float cachedSpeed = at<float>(at<void*>(g_gameDataMgr, 0x14), 0x58);\n    void* character =")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("mover_get_input_speed.py"),
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
