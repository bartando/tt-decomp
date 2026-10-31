"""Behavioral mutation proof for spin classification and character trail values.

Run from the repo root with PYTHONPATH=tools/lift-check and the lift-check venv.
Only exit 1 (behavioral FAIL) counts; build/spec failures do not.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

SOURCE = "src/game/ball/ball_shot.cpp"
CASES = [
    ("ball_classify_spin", "int pongBall_ClassifySpin(", [
        ("empty classification", "    const float direction =", "    return 8;\n    const float direction ="),
        ("wrong travel axis", "velocity->z >", "velocity->x >"),
        ("include zero as forward travel", "velocity->z >", "velocity->z >="),
        ("wrong spin axis", "const float x = spin->x", "const float x = spin->y"),
        ("invert camera side", "cameraSide == static_cast<uint8_t>(backwards)",
         "cameraSide != static_cast<uint8_t>(backwards)"),
        ("normalize camera byte", "cameraSide == static_cast<uint8_t>(backwards)",
         "(cameraSide != 0) == backwards"),
        ("wrong positive diagonal", "return 7;", "return 5;"),
        ("lose neutral direction", "    return 8;", "    return 0;"),
    ]),
    ("ball_trail_hit_value", "float game_2508(", [
        ("empty strength", "    const unsigned direction =", "    return 0.0f;\n    const unsigned direction ="),
        ("wrong neutral strength", "if (direction > 7) return g_kFloatConst_D110;",
         "if (direction > 7) return g_kFloatConst_D108;"),
        ("wrong selected slot", "static_cast<uint32_t>(g_currentInputSlot)", "0"),
        ("skip diagonal lookup", "static_cast<TrailCharacterView*>(pongMatch_GetCharacterForSlot(match, slot));\n    const float axial",
         "first;\n    const float axial"),
        ("wrong axial character", "? first->trail->topSpin : first->trail->backSpin;",
         "? second->trail->topSpin : second->trail->backSpin;"),
        ("wrong side strength", "second->trail->sideSpin + axial", "second->trail->backSpin + axial"),
        ("omit average", "combined * g_kFloatConst_D10C", "combined"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        if source.find(";", start) < source.find("{", start):
            start = source.index(signature, start + len(signature))
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"missing mutation anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(
                    trials=256, seed=1, patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
