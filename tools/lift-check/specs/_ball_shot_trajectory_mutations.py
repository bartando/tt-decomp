"""Behavioral mutation proof for angle sampling and iterative trajectory lifts.
Run with PYTHONPATH=tools/lift-check and the real lift-check virtual environment.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("ball_shot_sample_angles", "void BallShot_SampleAngles(", [
        ("empty sampling", "    int count = 0;", "    return;\n    int count = 0;"),
        ("test all direction bits", "static_cast<uint8_t>(increasing) != 0", "increasing != 0"),
        ("sample empty interval", "angle < samples->highAngle", "angle <= samples->highAngle"),
        ("lose sample 32", "count >= 32", "count >= 31"),
        ("omit recursion reset", "g_shotSolveState = 0;", "g_shotSolveState = 9;"),
        ("wrong sample angle", "sample->angle = angle;", "sample->angle = speed;"),
        ("omit stack sample", "0, false, sample, speed, angle", "0, false, nullptr, speed, angle"),
        ("wrong stack flag", "0, false, sample, speed, angle", "0, true, sample, speed, angle"),
        ("omit decrease", "angle -= samples->step;", "angle += samples->step;"),
        ("omit speed clamp", "if (length > limit)", "if (false)"),
        ("clamp increasing side too", "angle += samples->step;", "sample->velocity.x = 0;\n                angle += samples->step;"),
        ("omit fourth lane clamp", "sample->velocity = MulVmx(normalized, Vec4{limit, limit, limit, limit});",
         "const float w = sample->velocity.w;\n                        sample->velocity = MulVmx(normalized, Vec4{limit, limit, limit, limit});\n                        sample->velocity.w = w;"),
        ("wrong final count", "samples->count = count;", "samples->count = count + 1;"),
    ]),

    ("ball_shot_solve_trajectory", "int BallShot_SolveTrajectory(", [
        ("empty solver", "    g_shotSolveState =", "    return 1;\n    g_shotSolveState ="),
        ("wrong recursion cap", "g_shotSolveState > 128", "g_shotSolveState > 127"),
        ("skip recursion increment", "static_cast<uint32_t>(g_shotSolveState) + 1u", "static_cast<uint32_t>(g_shotSolveState)"),
        ("wrong guard return", "        return 0;", "        return 1;"),
        ("omit guard direction", "start->z > target->z ? -speed : speed", "speed"),
        ("force maximum initial angle", "angle = excess >= 0.0f ? maximumAngle : initial;", "angle = maximumAngle;"),
        ("drop candidate w", "Vec4 candidate = *target;", "Vec4 candidate{};"),
        ("omit court side mirror", "start->z > 0.0f ? -yawCosRaw : yawCosRaw", "yawCosRaw"),
        ("wrong derivative scale", "const float derivativeScale = g_fastOrbitMul;", "const float derivativeScale = 1.0f;"),
        ("stop too soon", "constexpr float converged = 9.999999747378752e-05f;", "constexpr float converged = 0.5f;"),
        ("skip backtracking", "if (!(square < previousSquare) && iterations != 0)", "if (false)"),
        ("back out speed too", "speedStep *= 0.5f;", "speedStep *= 0.5f;\n            speed -= speedStep;"),
        ("lose best velocity", "bestVelocity = candidate;", "bestVelocity = *target;"),
        ("wrong pitch-vs-speed branch", "const bool varyPitch = firstByte == 0 && sample == nullptr;", "const bool varyPitch = firstByte == 0;"),
        ("wrong iteration cap", "iterations >= 64", "iterations >= 63"),
        ("omit radius in target repair", "const float radius = CurrentBallRadius();", "const float radius = 0.0f;"),
        ("wrong target dimension", "__builtin_fmaf(table->width, 0.5f, radius)", "__builtin_fmaf(table->depth, 0.5f, radius)"),
        ("omit target cushion", "const float cushion = g_ballDragCoef;", "const float cushion = 0.0f;"),
        ("omit table-surface offset", "table->height + g_ballTableSurfaceOffset", "table->height"),
        ("wrong sample flag", "sample->flags[1] = bestFlags[2];", "sample->flags[1] = bestFlags[1];"),
        ("overwrite untouched sample angle", "sample->secondMeasure = bestSecondMeasure;", "sample->secondMeasure = bestSecondMeasure;\n        sample->angle = angle;"),
        ("lose output w", "    *velocity = candidate;", "    velocity->x = candidate.x; velocity->y = candidate.y; velocity->z = candidate.z;"),
        ("ignore iteration failure", "return iterations < 64 ? 1 : 0;", "return 1;"),
    ]),
    ("ball_shot_solve_trajectory", "bool SolveCorrection(", [
        ("wrong determinant", "__builtin_fmaf(otherZ, yawX, -product)", "__builtin_fmaf(otherZ, yawX, product)"),
        ("wrong yaw correction", "__builtin_fmaf(otherZ, errorX, -xProduct)", "__builtin_fmaf(otherZ, errorZ, -xProduct)"),
        ("skip singular termination", "if (__builtin_fabsf(yawStep) < tiny && otherStep < tiny) return false;", "if (false) return false;"),
    ]),

]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_shot_trajectory.cpp").read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"missing mutation anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(
                    trials=128, seed=1, patches=((body, body.replace(old, new)),))).run()
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
