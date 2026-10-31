"""Reject lost unordered clamps, wrong curves and late float rounding."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_pose_ease_sine", "wrong upper clamp", "return 1.0f;", "return 0.0f;"),
    ("player_pose_ease_sine", "late angle rounding", "const float angle = value * 1.5707963705062866f;", "const double angle = double(value) * 1.5707963705062866;"),
    ("player_pose_ease_cosine", "lose unordered clamp", "!(value > 0.0f)", "value <= 0.0f"),
    ("player_pose_ease_cosine", "wrong complement", "return 1.0f - cosine;", "return cosine;"),
    ("player_pose_ease_smooth", "omit half scale", "shifted * 0.5f", "shifted"),
    ("player_pose_ease_smooth", "wrong phase", "value * 3.1415927410125732f", "value * 1.5707963705062866f"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    for spec, label, old, new in CASES:
        if spec.endswith("_sine"):
            path, signature = "src/physics/ph_physics.cpp", "float ph_ClampAndSin("
        else:
            path = "src/game/player/player_pose_easing.cpp"
            signature = "float " + ("util_B6F0(" if spec.endswith("cosine") else "cmSmoothRemap_B768(")
        source = (root / path).read_text()
        start = source.index(signature)
        end = source.index("\n}", start) + 2
        body = source[start:end]
        assert old in body, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((body, body.replace(old, new, 1)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
