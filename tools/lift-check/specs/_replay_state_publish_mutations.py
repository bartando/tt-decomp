import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("wrong request flag", "replay[0x68CFB]", "replay[0x68CFA]"),
    ("invert disabled flag", "replay[0x68CFE] == 0", "replay[0x68CFE] != 0"),
    ("ignore entries", "*reinterpret_cast<const uint16_t*>(list + 4) > 0", "true"),
    ("lose lockout", "if (context[0x24] != 0) return;", "/* lockout lost */"),
    ("publish wrong pointer", "load_ptr32<void>(replay, 0x68D00)", "load_ptr32<void>(replay, 0x68D10)"),
    ("wrong readiness", "requested && hasEntries", "requested || hasEntries"),
    ("omit valid flag", "context[0x1C] = 1;", "context[0x1C] = 0;"),
]

def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("replay_state_publish.py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        ok = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if ok else 'MISSED'} {label}: {first}", flush=True)
        if not ok:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
