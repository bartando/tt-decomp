"""Only behavioral FAIL counts for deliberately broken target/math lifts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("ph_clamped_acos", "lose unordered saturation", "!(value > -1.0f)", "value <= -1.0f"),
    ("ph_clamped_acos", "wrong lower clamp", "!(value > -1.0f)", "!(value > 0.0f)"),
    ("ph_clamped_acos", "wrong saturation", "value >= 1.0f) return 0.0f", "value >= 1.0f) return 1.0f"),
    ("ph_clamped_acos", "drop acos", "crt_acos(value)", "value"),
    ("player_apply_movement_target", "reverse gate", "&& !pongPlayer_CheckServeInput(player)", "&& pongPlayer_CheckServeInput(player)"),
    ("player_apply_movement_target", "wrong protection bit", "0x40) & 2", "0x40) & 4"),
    ("player_apply_movement_target", "lose squared speed", "= speedSquared;", "= speed;"),
    ("player_apply_movement_target", "lose contact", "0x18) = contact;", "0x18) = 0.0f;"),
    ("player_apply_movement_target", "wrong clear mask", "&= 0xF7;", "&= 0xF3;"),
]


def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
