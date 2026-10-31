"""Behavioral proof for mover delta orchestration and its real virtual calls."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong step selection", "difference >= 0.0f ? delta : time", "difference >= 0.0f ? time : delta"),
    ("process zero step", "if (amount > 0.0f)", "if (amount >= 0.0f)"),
    ("wrong quaternion getter", "rotation->GetQuaternion()", "translation->GetVector()"),
    ("omit current translation", "__builtin_memcpy(current + 12, translation->GetVector(), 16);", "translation->GetVector();"),
    ("wrong earlier sample time", "const float previousTime = time - amount;", "const float previousTime = time;"),
    ("wrong earlier rotation type", "earlierRotation.type = 6;", "earlierRotation.type = 5;"),
    ("wrong earlier translation type", "earlierTranslation.type = 5;", "earlierTranslation.type = 6;"),
    ("ignore channel failure", "&& LocomotionStateAnim_EvaluateChannel(clip, nullptr, &earlierTranslation, previousTime)", "|| LocomotionStateAnim_EvaluateChannel(clip, nullptr, &earlierTranslation, previousTime)"),
    ("omit inverse", "rage::mat44InverseAffineInPlace(previous);", "(void)previous;"),
    ("omit composition", "rage::mat44ComposeAffineInPlace(current, previous);", "(void)current;"),
    ("wrong rotation setter", "rotation->SetQuaternion(quaternion);", "rotation->SetVector(quaternion);"),
    ("wrong translation setter", "translation->SetVector(current + 12);", "translation->SetQuaternion(current + 12);"),
    ("omit translation reset", "translation->Reset();", "(void)translation;"),
    ("wrong reset return", "translation->Reset();\n    return 1;", "translation->Reset();\n    return 0;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/anim/clip_mover_delta.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert old in source, f"missing mutation anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("clip_mover_delta.py"),
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
