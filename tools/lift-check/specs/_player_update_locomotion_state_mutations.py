"""Behavioral mutation proof; edits only build-cache copies, never the lift.

Run from the repository root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_player_update_locomotion_state_mutations.py

Every variant runs the full 1000-trial spec (seed 1), stopping at the first
divergence. Only exit 1 counts: BUILD/SPEC/UNSUPPORTED cannot pass this proof.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = [
    ("empty stub", "    auto* state = reinterpret_cast<PlayerPoseState*>(player);",
     "    return;\n    auto* state = reinterpret_cast<PlayerPoseState*>(player);"),
    ("wrong highest priority", "if (pongPlayer_D660_g(state))", "if (pongPlayer_D6B8_g(state))"),
    ("retain stale blend weight", "    state->blendWeight = 0.0f;", "    state->blendWeight = 0.5f;"),
    ("special exports secondary", "exportPose(state->special, state->pose);", "exportPose(state->secondary, state->pose);"),
    ("wrong export vtable slot", "animation, 8)(animation, frame)", "animation, 4)(animation, frame)"),
    ("recovery ignores locomotion type", "at<int32_t>(loco, 36) == 3", "at<int32_t>(loco, 36) == 4"),
    ("recovery wrong locomotion flag", "at<int32_t>(loco, 32) == 1", "at<int32_t>(loco, 32) == 0"),
    ("recovery crossing excludes equality", "at<float>(recovery, 172) >= time", "at<float>(recovery, 172) > time"),
    ("recovery always copies locomotion", "if (recovery[44])", "if (true)"),
    ("wrong root slot", "state->slotIndex + 17", "state->slotIndex + 16"),
    ("root transform loses w addition", "i < 4; ++i) transform[12 + i]", "i < 3; ++i) transform[12 + i]"),
    ("wrong root basis", "transform[5] = 1.0f", "transform[5] = 0.0f"),
    ("omit root activation flag", "    state->locomotion[340] = 1;\n}", "    state->locomotion[340] = 0;\n}"),
    ("phase uses previous pose", "copyPose(state->pose, phase + 384);", "copyPose(state->pose, phase + 128);"),
    ("phase ignores suppression", "blend = state->suppressBlend == 0;", "blend = true;"),
    ("force wrong active slot", "state->activeSlot = state->defaultSlot", "state->activeSlot = nullptr"),
    ("omit swing time snapshot", "at<float>(swing, 24) = at<float>(swing, 28);", "at<float>(swing, 24) = 0.0f;"),
    ("skip swing pose helper", "        LocomotionStateAnim_AC40_g(swing, record);", "        (void)record;"),
    ("unsigned frame markers", "at<int16_t>(record, marker)", "at<uint16_t>(record, marker)"),
    ("wrong marker rate", "0.03333333507180214f", "0.01666666753590107f"),
    ("wrong auxiliary marker", "markerTime(record, 306)", "markerTime(record, 308)"),
    ("wrong timed transform stride", "state->slotIndex * 80", "state->slotIndex * 64"),
    ("drop timed activation flags", "transform, record[314]", "transform, 0"),
    ("keep finished active slot", "if (at<float>(swing, 28) >= at<float>(swing, 48))", "if (false)"),
    ("omit secondary overlay", "if (secondaryOverlay && pongPlayer_D6B8_g(state))", "if (false)"),
    ("omit secondary blend", "blend = progress < start;", "blend = false;"),
    ("NaN previous triggers recovery transition", "at<float>(recovery, 168) < time",
     "!(at<float>(recovery, 168) >= time)"),
    ("omit idle weight", "        state->blendWeight = 1.0f;", "        state->blendWeight = 0.0f;"),
    ("late ramp wrong denominator", "(progress - end) / (limit - end)", "(progress - end) / (1.0f - end)"),
    ("late ramp wrong threshold", "(ratio - 0.4f)", "(ratio - 0.5f)"),
    ("early ramp wrong ratio", "const float ratio = progress / start;", "const float ratio = progress;"),
    ("wrong early channel curve", "ratio * 2.0f", "ratio * 1.0f"),
    ("wrong easing selector", "case 1: weight = util_B6F0(weight)", "case 1: weight = phBoundCapsule_B6A0_g(weight)"),
    ("drop blend filter", "nullptr, filter, filterData, weight", "nullptr, nullptr, filterData, weight"),
    ("secondary overlay wrong scratch", "state->pose, state->secondaryPose,", "state->pose, state->pose,"),
    ("omit auxiliary postprocess", "if (state->auxiliary) LocomotionStateAnim_1E68_g", "if (false) LocomotionStateAnim_1E68_g"),
    ("omit final additive frame", "if (state->additivePose) copyPose", "if (false) copyPose"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_animation_state.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("player_update_locomotion_state.py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
