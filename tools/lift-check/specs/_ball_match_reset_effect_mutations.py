"""Behavioral mutation proof for the reset misname fix and hit trail lift.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_match_reset_effect_mutations.py
Builds patched cache copies; never changes repository sources. Only exit 1 counts.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("bp_reset", "src/game/ball/ball_predict.cpp", "void gdBallPredictData::Reset(", [
        ("omit sample count reset", "m_count = 0;", "m_count = 1;"),
        ("leave one ID", "i < m_idCount", "i + 1 < m_idCount"),
        ("copy only callback target", "i < 4", "i < 1"),
        ("lose time sentinel", "m_idTime = -1.0f;", "m_idTime = 0.0f;"),
    ]),
    ("match_game_3860", "src/game/match/pong_match.cpp", "void game_3860(", [
        ("skip shared reset", "state->m_pBallPredict->Reset(name);", "(void)name;"),
        ("wrong callback target", "reinterpret_cast<uintptr_t>(gameState)", "uintptr_t{0}"),
        ("wrong callback kind", "        4,", "        1,"),
    ]),
    ("ball_set_hit_effect", "src/game/ball/pong_ball.cpp", "void game_2010(", [
        ("ignore input low-byte ABI", "static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr))", "io_Input_poll_9D68(g_input_obj_ptr)"),
        ("wrong local mode", "lbl_825C9A2C == 0", "lbl_825C9A2C == 1"),
        ("wrong option", "lbl_825C5EC8.hitTrailEnabled", "lbl_825C5EC8.flag30"),
        ("skip second trail", "i < 2", "i < 1"),
        ("drop intensity", "type, intensity, lbl_82630710", "type, 0, lbl_82630710"),
        ("skip reset", "reinterpret_cast<gmball::HitTrailView*>(node->trails[i])->Reset();", "(void)node;"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, path, signature, mutants in CASES:
        source = (root / path).read_text()
        start = source.index(signature)
        while source.find(";", start) < source.find("{", start):
            start = source.index(signature, start + len(signature))
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutants:
            assert old in body, f"missing anchor: {spec}: {label}"
            for seed in (1, 2):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(trials=128, seed=seed,
                                         patches=((body, body.replace(old, new)),))).run()
                first = output.getvalue().splitlines()[0]
                print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: seed {seed}: {first}", flush=True)
                if rc != 1:
                    print(output.getvalue())
                    return 1
                total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
