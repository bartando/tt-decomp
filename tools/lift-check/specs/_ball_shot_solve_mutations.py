"""Behavioral mutation proof for the complete BallShot_Solve orchestration.
Run with PYTHONPATH=tools/lift-check and the lift-check virtual environment.
Only behavioral FAIL (exit 1) counts as a caught mutation.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("empty solve", "    auto* entry =", "    return 1;\n    auto* entry ="),
    ("skip recursion counter reset", "    g_shotSolveState = 0;", "    g_shotSolveState = 17;"),
    ("invert all-lane angle", "allGreater ? -0x1.921fb6p-4f : 0x1.921fb6p+0f",
     "allGreater ? 0x1.921fb6p+0f : -0x1.921fb6p-4f"),
    ("omit ball radius", "raisedTarget.y = BallHeight();",
     "raisedTarget.y = static_cast<const SolveTable*>(g_pTableDims)->height;"),
    ("wrong stack flag", "false, nullptr, speed", "true, nullptr, speed"),
    ("wrong stack sample pointer", "false, nullptr, speed",
     "false, reinterpret_cast<SolveSample*>(velocity), speed"),
    ("omit special swing 11", "entry->swingType == 6 || entry->swingType == 11", "entry->swingType == 6"),
    ("wrong horizontal projection", "horizontal.y = 0.0f;", "horizontal.x = 0.0f;"),
    ("wrong upper angle bound", "increasing.highAngle = entry->maxAngle;", "increasing.highAngle = angle;"),
    ("omit sample-step epsilon", "step, -epsilon", "step, 0.0f"),
    ("wrong lower bound", "? 0.0f : 0.009999999776482582f", "? 0.009999999776482582f : 0.0f"),
    ("cache pre-solver height", "start->y > BallHeight()", "start->y > raisedTarget.y"),
    ("wrong active entry", "g_ballSplashArray + slot * 0x1A0u + 0x60",
     "static_cast<const uint8_t*>(entryPtr) + 0x60"),
    ("wrong sample-count gate", "if (increasing.count <= 0)", "if (decreasing.count <= 0)"),
    ("wrong negative set", "chosen = &decreasing.samples[magnitude];", "chosen = &increasing.samples[magnitude];"),
    ("omit backwards search", "while (index > 0 && !(chosen->angle < threshold))", "while (false)"),
    ("reverse angle threshold", "chosen->angle < threshold", "chosen->angle > threshold"),
    ("wrong selected angle", "entry->chosenAngle = chosen->angle;", "entry->chosenAngle = angle;"),
    ("overwrite untouched velocity w", "    velocity->z = chosen->velocity.z;",
     "    velocity->z = chosen->velocity.z;\n    velocity->w = chosen->velocity.w;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_shot_solve.cpp").read_text()
    start = source.index("int BallShot_Solve(")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    for label, old, new in MUTATIONS:
        assert old in body, f"missing mutation anchor: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ball_shot_solve.py"), Options(
                trials=256, seed=1, patches=((body, body.replace(old, new)),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
