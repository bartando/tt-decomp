"""Mutations of the two mode-reset helper lifts."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("player_reset_animation_slot", [
        ("omit base reset", "static_cast<LocomotionStateAnim*>(object)->ResetAccumulators();", "(void)object;"),
        ("leave third vector", "offset <= 0xB0", "offset < 0xB0"),
        ("overwrite basis w", "lane < 3", "lane < 4"),
        ("wrong slot marker", "0x130) = 0xFFFF", "0x130) = 0"),
        ("wrong default flags", "0x139) = 0x13", "0x139) = 0"),
    ]),
    ("player_select_face_animation", [
        ("test canonical alternate only", "at<uint8_t>(g_loop_obj_ptr, 0x240) != 0", "at<uint8_t>(g_loop_obj_ptr, 0x240) == 1"),
        ("leave old timer", "at<float>(current, 0x14) = 0.0f", "at<float>(current, 0x14) = 1.0f"),
        ("ignore selection guard", "g_faceAnimationSelectionGuard[1] != 0", "false"),
        ("drop RNG carry", " + g_prngState[1]", ""),
        ("allow neutral slot", "% (count - 1) + 1", "% count"),
        ("wrong RNG sign mask", "& 0x7FFFFFFF", "& 0x7FFFFF"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_animation_reset_helpers.cpp").read_text()
    total = 0
    for spec, mutations in CASES:
        for label, old, new in mutations:
            assert old in source, label
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, trials=1000, patches=((source, source.replace(old, new)),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
