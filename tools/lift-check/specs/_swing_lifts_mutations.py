"""Check that the swing specs reject broken lifts (only behavioral FAIL counts).

Run with the lift-check Python and PYTHONPATH=tools/lift-check. Each mutant uses
its spec's default 1000 trials, seed 1; the normal specs also run with seed 7.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

SWING = "src/game/player/pong_player_swing.cpp"
PLAYER = "src/game/player/pong_player.cpp"
CASES = [
    ("player_compute_swing_strength", SWING, 'extern "C" void pongPlayer_42E0_g', [
        ("wrong default power", "*strength = 0.0f;", "*strength = 1.0f;"),
        ("omit virtual strength", "m_swingType == 9", "m_swingType == 8"),
        ("omit half scaling", "0.5f), power)", "1.0f), power)"),
    ]),
    ("player_process_swing_input", SWING, 'extern "C" uint32_t pongPlayer_73E8_g', [
        ("ignore low-byte poll", "static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr))", "io_Input_poll_9D68(g_input_obj_ptr)"),
        ("drop fourth vector lane", "sizeof(target));", "12);"),
        ("lose fallback return", "return pg_C7A0_g(animation, inputValue);", "pg_C7A0_g(animation, inputValue); return 0;"),
    ]),
    ("player_predict_position", SWING, 'extern "C" vec3* pongPlayer_AB48_g', [
        ("omit court clamp", "position->x = clampCourt(position->x, lower.x, upper.x);", "position->x = position->x;"),
        ("lose destination return", "return position;", "return nullptr;"),
    ]),
    ("player_transform_court_bounds", PLAYER, 'extern "C" void pongPlayer_8B90_fw', [
        ("wrong side index", "const int sideIndex = *reinterpret_cast<int32_t*>(base + 0x190);", "const int sideIndex = 0;"),
        ("wrong court output", "sideIndex, outPos, outVel", "sideIndex, outPos, outPos"),
        ("omit corner swap", "if (outPos->x > outVel->x || outPos->z > outVel->z)", "if (false)"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    count = 0
    for spec, path, signature, mutations in CASES:
        source = (root / path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"missing mutation anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
