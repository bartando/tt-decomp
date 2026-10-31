"""Behavioral mutation proof for the complete replay-record queue chain.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_replay_mutations.py
Only behavioral FAIL (exit 1) counts. Patches modify cached builds only.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/ball/ball_replay.cpp"
CASES = [
    ("ball_replay_append_sample", "bool BallReplay_AppendSample(", [
        ("empty append", "    auto* queue =", "    return false;\n    auto* queue ="),
        ("broaden full gate", "queue->count == kReplayCapacity", "queue->count >= kReplayCapacity"),
        ("wrong head wrap", "queue->head == kReplayCapacity", "queue->head == kReplayCapacity - 1"),
        ("skip head increment", "++queue->head;", "(void)queue;"),
    ]),
    ("ball_replay_append_sample", "void CopyReplaySample(", [
        ("overwrite padding", "__builtin_memcpy(&destination.time, &source.time, 4);", "__builtin_memcpy(&destination, &source, sizeof(source));"),
        ("lose angular vector", "destination.angVel = source.angVel;", "(void)source;"),
    ]),
    ("ball_replay_find_neighbors", "bool BallReplay_FindNeighborIndices(", [
        ("succeed on empty", "        return false;", "        return true;"),
        ("wrong endpoint", "*first = endCount - 2;", "*first = endCount - 1;"),
        ("wrong factor", "time - queue->At(i).time", "time - queue->At(i + 1).time"),
        ("wrong second index", "*second = i + 1;", "*second = i;"),
    ]),
    ("ball_replay_insert_sample", "void BallReplay_InsertSample(", [
        ("omit duplicate-last append", "BallReplay_AppendSample(queue, &queue->At(queue->count - 1));", "(void)queue;"),
        ("wrong shift source", "queue->At(i), queue->At(i - 1)", "queue->At(i), queue->At(i)"),
        ("wrong insertion index", "queue->At(index), *sample", "queue->At(index + 1), *sample"),
        ("snapshot aliased source too early", "    BallReplay_AppendSample(queue, &queue->At(queue->count - 1));", "    bpReplayBall snapshot = *sample;\n    sample = &snapshot;\n    BallReplay_AppendSample(queue, &queue->At(queue->count - 1));"),
    ]),
    ("ball_replay_insert_timed_sample", "void BallReplay_InsertTimedSample(", [
        ("exclude equal and unordered times", "!(time > queue->At(count - 1).time)", "time < queue->At(count - 1).time"),
        ("lose unordered singleton insert", "!(time >= queue->At(0).time)", "time < queue->At(0).time"),
        ("skip duplicate timestamps", "while (second < count && time ==", "while (false && time =="),
    ]),
    ("ball_replay_record_ball_sample", "void gdReplayMgr_RecordBallSample(", [
        ("do not evict full ring", "queue->count == kReplayCapacity", "false"),
        ("wrong tail wrap", "queue->tail == kReplayCapacity", "queue->tail == kReplayCapacity - 1"),
        ("lose eviction count", "--queue->count;", "(void)queue;"),
    ]),
    ("ball_replay_remove_sample", "void BallReplay_RemoveSample(", [
        ("skip compaction", "next < queue->count", "false"),
        ("wrong shift source", "queue->At(next - 1), queue->At(next)", "queue->At(next - 1), queue->At(next - 1)"),
        ("lose count decrement", "--queue->count;", "(void)queue;"),
        ("wrong head wrap", "kReplayCapacity - 1 : queue->head - 1", "0 : queue->head - 1"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    total = 0
    for spec, signature, mutants in CASES:
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
