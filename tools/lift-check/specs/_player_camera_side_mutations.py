"""Every cache-only camera-side mutant must produce behavioral FAIL (exit 1)."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("either mode selects alternate", "                        &&", "                        ||"),
    ("truncate first mode", "at<int32_t>(g_input_obj_ptr, 0x38)", "at<uint8_t>(g_input_obj_ptr, 0x3B)"),
    ("reverse camera indices", "alternate ? 0x0C : 0x08", "alternate ? 0x08 : 0x0C"),
    ("wrong sentinel fallback", "if (index == -1) return 1;", "if (index == -1) return 0;"),
    ("wrong null-node fallback", "if (!node) return 1;", "if (!node) return 0;"),
    ("wrong failed-cast fallback", "if (!record) return 1;", "if (!record) return 0;"),
    ("omit checked cast", "void* record = game_1700(node);", "void* record = node;"),
    ("read only low flag byte", "at<uint32_t>(record, 0x30)", "at<uint8_t>(record, 0x33)"),
    ("reverse side flag", "at<uint32_t>(record, 0x30) == 0", "at<uint32_t>(record, 0x30) != 0"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_camera_side.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, f"missing mutation anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_camera_side.py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
