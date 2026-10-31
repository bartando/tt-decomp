"""Behavioral mutation checks for the auxiliary player pose update."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("ignore enable byte", "!at<uint8_t>(auxiliary, 4)", "false"),
    ("ignore primary guard", "at<uint32_t>(g_matMgrGuard, 4) != 0", "false"),
    ("ignore blend guard", "g_auxiliaryPoseBlendGuard[1] == 0", "true"),
    ("miss deadline equality", ">= deadline", "> deadline"),
    ("wrong payload words", "(std::strlen(name) + 4) >> 2", "std::strlen(name) >> 2"),
    ("leave deadline latched", "at<float>(auxiliary, 0x18) = 0.0f", "at<float>(auxiliary, 0x18) = 1.0f"),
    ("wrong pose weight", "1.0f, nullptr, LocomotionStateAnim_BB98", "0.5f, nullptr, LocomotionStateAnim_BB98"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_auxiliary_pose.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_update_auxiliary_pose.py"),
                         Options(seed=1, trials=1000, patches=((source, source.replace(old, new)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
