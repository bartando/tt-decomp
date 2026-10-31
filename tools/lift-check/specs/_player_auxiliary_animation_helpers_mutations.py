"""Reject intentional regressions in auxiliary-layer animation helpers."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("player_update_random_auxiliary_animation", [
        ("reverse timer direction", "- g_sysTimeManager.frameSeconds", "+ g_sysTimeManager.frameSeconds"),
        ("redraw unordered timer", "if (timer < 0.0f)", "if (!(timer >= 0.0f))"),
        ("drop RNG carry", " + g_prngState[1]", ""),
        ("always choose first entry", "(nextRandom() & 0x7FFFFFFF) % count", "0u"),
        ("omit face filter", "blendFrame(state, 0x38, LocomotionStateAnim_81A8", "blendFrame(state, 0x38, nullptr"),
        ("keep completed queued animation", "at<void*>(state, 0x50) = nullptr", "at<void*>(state, 0x50) = state"),
    ]),
    ("player_update_active_auxiliary_animation", [
        ("ignore notification latch", "&& !g_faceAnimDirty", "&& true"),
        ("wrong impending completion event", "PostGameMessage(0x580F", "PostGameMessage(0x580D"),
        ("lose completion event", "PostGameMessage(0x580E", "PostGameMessage(0x580D"),
        ("leave active pointer", "at<void*>(state, 0x44) = nullptr", "at<void*>(state, 0x44) = state"),
        ("omit recipient class bit", "(bit & 0xFF) | 0x40", "(bit & 0xFF)"),
        ("omit weight clamp", "return double(nonnegative) - 1.0 >= 0.0 ? 1.0f : nonnegative;", "return raw;"),
    ]),
    ("player_refresh_auxiliary_animation", [
        ("lose normalized clip phase", "at<float>(bundle, 0x0C) * at<float>(base, 0x14)", "at<float>(bundle, 0x0C)"),
        ("skip base advancement", "LocomotionStateAnim_28B0_w(base);", "(void)base;"),
        ("omit active weight inversion", "weight = 1.0f - blendFactor(state, active)", "weight = blendFactor(state, active)"),
        ("blend unordered weight", "if (weight > 0.0f)", "if (!(weight <= 0.0f))"),
        ("use wrong blend frame", "nullptr, weight, 0x38)", "nullptr, weight, 0x34)"),
        ("blend instead of final copy", "0.0f, nullptr, playerPose_CopyDof", "0.0f, nullptr, LocomotionStateAnim_BB98"),
    ]),
    ("player_pose_copy_dof", [
        ("copy self", "->CopyFrom(source)", "->CopyFrom(destination)"),
        ("wrong virtual slot", "    virtual void Reserved5() = 0;\n", ""),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_auxiliary_animation_helpers.cpp").read_text()
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
