"""Prove the two phase specs reject behavioral defects in cache-only variants.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_player_swing_phase_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("player_start_swing_phase", [
        ("ignore phase gate", "at<float>(state, 0x19C) <= 0.0f", "true"),
        ("wrong active flag", "at<uint16_t>(state, 0x5A) & 1", "at<uint16_t>(state, 0x5A) & 2"),
        ("start wrong clip", " + 0x10, clip, 0)", " + 0x10, state, 0)"),
        ("truncate start result", "return result;", "return static_cast<uint8_t>(result);"),
        ("ignore low-byte result", "static_cast<uint8_t>(result)", "result"),
        ("normalize NaN input", "inputTime > 0.0f", "!(inputTime <= 0.0f)"),
        ("drop phase cap", "? 1.0f : float(nonnegative)", "? 2.0f : float(nonnegative)"),
        ("omit previous phase", "at<float>(state, 0x64) = phase;", "(void)phase;"),
        ("wrong event", "PostGameMessage(0x1011,", "PostGameMessage(0x1012,"),
        ("wrong slot mask", "1u << shift", "2u << shift"),
    ]),
    ("player_swing_blend_marker", [
        ("unsigned marker", "at<int32_t>(record, 0x38)", "at<uint32_t>(record, 0x38)"),
        ("wrong frame rate", "0.03333333507180214f", "0.01666666753590107f"),
        ("omit duration", "return seconds / duration;", "return seconds;"),
        ("accept NaN duration", "if (!(duration > 0.0f))", "if (duration <= 0.0f)"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_swing_phase.cpp").read_text()
    count = 0
    for spec, mutations in CASES:
        for label, old, new in mutations:
            assert old in source, f"missing mutation anchor: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
