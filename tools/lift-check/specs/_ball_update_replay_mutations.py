"""Behavioral mutation proof for replay pose orchestration.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_update_replay_mutations.py
Only behavioral FAIL counts. Patches modify cached builds only.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_replay_update.cpp").read_text()
    start = source.index("void gmBallNode_UpdateReplay(")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    mutants = [
        ("empty lift", "    using namespace ballReplayUpdate;", "    return;\n    using namespace ballReplayUpdate;"),
        ("wrong replay elapsed", "replay->time - replay->previousTime", "replay->time + replay->previousTime"),
        ("drop replay position", "__builtin_memcpy(&matrix.d, &replay->current.pos, sizeof(matrix.d));", "(void)replay;"),
        ("drop position W", "sizeof(matrix.d)", "12"),
        ("wrong spin vector", "&replay->current.angVel.x", "&replay->current.pos.x"),
        ("retain instance across spin", "    instance = reinterpret_cast<Instance*>(node->inst);\n    instance->SetPreviousMatrix", "    instance->SetPreviousMatrix"),
        ("store new pose as previous", "SetPreviousMatrix(&instance->matrix)", "SetPreviousMatrix(&matrix)"),
        ("retain instance across callback", "    instance = reinterpret_cast<Instance*>(node->inst);\n    instance->matrix = matrix;", "    instance->matrix = matrix;"),
        ("copy only first row", "instance->matrix = matrix;", "instance->matrix.a = matrix.a;"),
        ("lose level handle", "reinterpret_cast<Instance*>(node->inst)->levelIndex", "0"),
    ]
    for label, old, new in mutants:
        assert old in body, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ball_update_replay.py"), Options(
                trials=128, seed=1, patches=((body, body.replace(old, new)),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(mutants)}/{len(mutants)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
