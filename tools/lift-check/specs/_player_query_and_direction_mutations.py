import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_serve_state_query", "ignore low-byte gate", "static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr)) == 0", "io_Input_poll_9D68(g_input_obj_ptr) == 0"),
    ("player_serve_state_query", "wrong serve field", "bytes + 0x17EC", "bytes + 0x17E8"),
    ("player_serve_state_query", "invert active state", "bytes + 0x17EC) != 0", "bytes + 0x17EC) == 0"),
    ("player_serve_state_query", "leave inactive output", "*answer = 0;", "*answer = 1;"),
    ("player_ai_swing_direction", "wrong resolved gate", "direction->resolved != 0", "direction->resolved == 1"),
    ("player_ai_swing_direction", "lose signed zero", "range.value >= 0.0f ? valueBits", "range.value > 0.0f ? valueBits"),
    ("player_ai_swing_direction", "wrong upper clamp", "? maximumBits : lowerBits", "? lowerBits : maximumBits"),
    ("player_ai_swing_direction", "wrong MWC multiplier", "0x5CDCFAA7u", "0x5CDCFAA9u"),
    ("player_ai_swing_direction", "drop MWC carry", "* 0x5CDCFAA7u + g_prngState[1]", "* 0x5CDCFAA7u"),
    ("player_ai_swing_direction", "wrong sample bits", "& 0x7FFFFFu", "& 0x3FFFFFu"),
    ("player_ai_swing_direction", "wrong first weight", "const float p0 = scale * w0", "const float p0 = scale * w1"),
    ("player_ai_swing_direction", "wrong direction priority", "else if (direction->downSelected != 0)", "if (direction->downSelected != 0)"),
    ("player_ai_swing_direction", "omit resolved flag", "direction->resolved = 1;", "direction->resolved = 0;"),
]

def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"), Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
