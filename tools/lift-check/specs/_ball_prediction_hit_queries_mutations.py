"""Mutation checks for the five classifier queries; only behavioral FAIL counts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_hit_queries_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("ball_predict_find_net_contact", "int BallPredict_FindNetContact(", [
        ("empty query", "    for (int i = from;", "    return -1;\n    for (int i = from;"),
        ("skip first candidate", "int i = from;", "int i = from + 1;"),
        ("allow floor equality", "sample.pos.y <= 0.0f", "sample.pos.y < 0.0f"),
        ("reject unordered height", "sample.pos.y <= 0.0f", "!(sample.pos.y > 0.0f)"),
        ("test table flag instead", "sample.flag9 != 0", "sample.bounced != 0"),
    ]),
    ("ball_predict_find_return_across_net", "int BallPredict_FindReturnAcrossNet(", [
        ("omit zero-z early out", "if (initialZ == 0.0f) return -1;", "(void)initialZ;"),
        ("invert target side", "initialZ < 0.0f", "initialZ > 0.0f"),
        ("include initial sample", "int i = from + 1;", "int i = from;"),
        ("allow floor equality", "sample.pos.y <= 0.0f", "sample.pos.y < 0.0f"),
        ("classify zero-z as positive", "sample.pos.z > 0.0f", "sample.pos.z >= 0.0f"),
    ]),
    ("ball_predict_find_bounce_on_side", "int BallPredict_FindBounceOnSide(", [
        ("wrong no-contact code", "    return -3;", "    return -1;"),
        ("accept contacts before air", "else if (airborne)", "else if (true)"),
        ("omit airborne tracking", "airborne = true;", "airborne = false;"),
        ("wrong side sign", "sample.pos.z < 0.0f", "sample.pos.z > 0.0f"),
        ("test all side bits", "static_cast<uint8_t>(negativeSide)", "negativeSide"),
        ("wrong side-mismatch code", "? i : -2", "? i : -1"),
    ]),
    ("ball_predict_find_departing_sample", "int BallPredict_FindDepartingSample(", [
        ("full width instead of half", "table->width * 0.5f", "table->width"),
        ("include positive-x boundary", "sample.pos.x > halfWidth", "sample.pos.x >= halfWidth"),
        ("ignore outward x direction", "sample.vel.x > 0.0f", "sample.vel.x < 0.0f"),
        ("ignore negative-z exit", "if (sample.pos.z < table->length * -0.5f && sample.vel.z < 0.0f) return i;", "(void)sample.pos.z;"),
        ("wrong descending-height gate", "sample.pos.y < table->height", "sample.pos.y <= table->height"),
    ]),
    ("ball_predict_needs_outcome_forecast", "uint32_t BallPredict_NeedsOutcomeForecast(", [
        ("always forecast", "    const auto* table =", "    return 1;\n    const auto* table ="),
        ("omit floor margin", "table->height - 0.10000000149011612f", "table->height"),
        ("use numeric z sign", "SignBit(last.pos.z) == SignBit(last.vel.z)", "(last.pos.z < 0.0f) == (last.vel.z < 0.0f)"),
        ("include z margin equality", "__builtin_fabsf(last.pos.z) > zLimit", "__builtin_fabsf(last.pos.z) >= zLimit"),
        ("use zero instead of side threshold", "last.pos.z < lbl_825C5938", "last.pos.z < 0.0f"),
        ("test all side bits", "static_cast<uint8_t>(negativeSide)", "negativeSide"),
        ("ignore x travel direction", "SignBit(last.pos.x) == SignBit(last.vel.x)", "true"),
        ("include x margin equality", "__builtin_fabsf(last.pos.x) > xLimit", "__builtin_fabsf(last.pos.x) >= xLimit"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_prediction_hit_queries.cpp").read_text()
    count = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=800, seed=1,
                                     patches=((body, body.replace(old, new)),))).run()
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
