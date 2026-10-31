"""Behavioral mutation checks for recovered network helpers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "ball_copy_shot_locked": ("src/game/ball/ball_process_hit.cpp", [
        ("skip copy", "ballPredict_CopyShot(reinterpret_cast<bpShot*>(bytes + 0x40), shot);", "(void)shot;"),
        ("wrong destination", "bytes + 0x40), shot", "bytes + 0x30), shot"),
        ("wrong unlock value", "bytes[0x104] = 1;", "bytes[0x104] = 0;"),
        ("wrong enabled flag", "if (bytes[0x105])", "if (bytes[0x104])"),
        ("drop diagnostics", 'nop_8240E6D0("Cannot Lock when Unlock is not enabled");' , "(void)0;"),
    ]),
}

def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, (path, mutations) in CASES.items():
        source = (root / path).read_text()
        for label, old, new in mutations:
            assert old in source, label
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=128, seed=1, patches=((old, new),))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
