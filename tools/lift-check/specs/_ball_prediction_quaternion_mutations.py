"""Behavioral proof for the new quaternion angle/slerp and shared normalizer.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_quaternion_mutations.py
Only behavioral FAIL (exit 1) counts; patches alter cached builds only.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

QUATERNION = "src/game/ball/ball_prediction_quaternion.cpp"
CASES = [
    ("ball_predict_quaternion_angle", QUATERNION, "float BallPredict_QuaternionAngle(", [
        ("zero angle", "    float dot =", "    return 0.0f;\n    float dot ="),
        ("wrong dot lane", "second->z * first->z", "second->z * first->y"),
        ("lose absolute dot", "crt_acos(__builtin_fabsf(dot))", "crt_acos(dot)"),
        ("wrong angular scale", "angle * g_lookAtMultiplier", "angle"),
        ("skip unordered angle", "!(dot <= lbl_825C5938) && !(dot >= g_kFloatConst_D108)", "dot > lbl_825C5938 && dot < g_kFloatConst_D108"),
        ("include unit endpoint", "!(dot >= g_kFloatConst_D108)", "!(dot > g_kFloatConst_D108)"),
    ]),
    ("ball_predict_quaternion_slerp", QUATERNION, "void BallPredict_QuaternionSlerp(", [
        ("empty slerp", "    const float halfAngle =", "    return;\n    const float halfAngle ="),
        ("lose half angle", "* g_kFloatConst_D10C;", "* g_kFloatConst_D108;"),
        ("copy wrong singular source", "*out = *first;", "*out = *second;"),
        ("ignore interpolation factor", "halfAngle * factor", "halfAngle"),
        ("drop second weight reciprocal", "static_cast<float>(crt_sin(scaledAngle)) * reciprocal", "static_cast<float>(crt_sin(scaledAngle))"),
        ("wrong first weight angle", "crt_sin(halfAngle - scaledAngle)", "crt_sin(scaledAngle)"),
        ("skip quaternion W", "out->w = __builtin_fmaf(second->w, secondWeight, first->w * firstWeight);", "(void)out;"),
        ("skip normalization", "rage::NormalizeQuaternion(&out->x);", "(void)out;"),
    ]),
    # These are the existing normalizer's four behavioral mutation cases.
    ("normalize_quaternion", "src/rage/animation/rage_anim.cpp", "void NormalizeQuaternion(", [
        ("wrong fused lane", "__builtin_fmaf(quat[2], quat[2], magSquared)", "__builtin_fmaf(quat[1], quat[1], magSquared)"),
        ("missing lane write", "quat[3] *= invMag;", "(void)invMag;"),
        ("zero magnitude skips writes", "quat[0] *= invMag;", "if (magSquared != 0.0f) quat[0] *= invMag;"),
        ("wrong scale", "1.0f / std::sqrt(magSquared) : 0.0f", "2.0f / std::sqrt(magSquared) : 0.0f"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, path, signature, mutants in CASES:
        source = (root / path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutants:
            assert old in body, f"missing anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(
                    trials=128, seed=1, patches=((body, body.replace(old, new)),))).run()
            first_line = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {first_line}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
