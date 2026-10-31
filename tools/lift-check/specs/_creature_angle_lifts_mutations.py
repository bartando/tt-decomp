"""Mutation proof for the wrapped creature angular limits.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_angle_lifts_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("creature_wrap_angle", "src/anim/angle_helpers.cpp", "float LocomotionStateAnim_WrapAngle(", [
        ("empty lift", "    const float offset", "    return 0.0f;\n    const float offset"),
        ("wrong negative offset", "value < 0.0f ? -kPi : kPi", "kPi"),
        ("skip float shift rounding", "const float shifted = offset + value", "const double shifted = double(offset) + value"),
        ("wrong remainder period", "double(kTwoPi)", "double(kPi)"),
        ("retain minus pi", "return result == -kPi ? kPi : result", "return result"),
    ]),
    ("creature_is_angle_closer", "src/anim/angle_helpers.cpp", "bool LocomotionStateAnim::IsAngleCloser(", [
        ("empty lift", "    const float first", "    return false;\n    const float first"),
        ("straight first distance", "LocomotionStateAnim_WrapAngle(target - angle2)", "(target - angle2)"),
        ("reverse first subtraction", "target - angle2", "angle2 - target"),
        ("accept ties", "__builtin_fabsf(first) < __builtin_fabsf(second)", "__builtin_fabsf(first) <= __builtin_fabsf(second)"),
        ("accept unordered distances", "__builtin_fabsf(first) < __builtin_fabsf(second)", "!(__builtin_fabsf(first) >= __builtin_fabsf(second))"),
    ]),
    ("creature_clamp_angle", "src/anim/angle_helpers.cpp", "float LocomotionStateAnim_A1F8_g(", [
        ("empty lift", "    const float wrapped", "    return 0.0f;\n    const float wrapped"),
        ("skip input wrapping", "LocomotionStateAnim_WrapAngle(value)", "value"),
        ("bypass at span equality", "> kFullTurnThreshold", ">= kFullTurnThreshold"),
        ("omit full-span bypass", "__builtin_fabsf(rangeMax - rangeMin) > kFullTurnThreshold", "false"),
        ("skip minimum wrapping", "LocomotionStateAnim_WrapAngle(rangeMin)", "rangeMin"),
        ("reverse crossing gate", "if (high < low)", "if (high > low)"),
        ("reject endpoint equality", "wrapped <= high)", "wrapped < high)"),
        ("reverse nearer endpoint", "? low : high", "? high : low"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        # Skip declarations: each definition begins at column zero.
        start = source.index("\n" + signature) + 1
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) >= 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec}: {label}: BUILD {exc}", flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and "faulted" not in report
            first = report.splitlines()[0] if report else "no checker output"
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(report)
                return 1
        total += len(mutations)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
