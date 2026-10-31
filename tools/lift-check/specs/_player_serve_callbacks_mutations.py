"""Behavioral mutation proof for serve callback helpers (cache-only patches)."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("player_serve_callback_busy", [
        ("query absent callback", "if (at<int32_t>(blender, 0x6C) == 0)", "if (false)"),
        ("truncate callback kind", "at<int32_t>(blender, 0x6C)", "at<uint8_t>(blender, 0x6F)"),
        ("wrong callback", ") + 0x60, &busy", ") + 0x50, &busy"),
        ("require exactly one", "return busy != 0;", "return busy == 1;"),
    ]),
    ("player_reset_serve_input_events", [
        ("ignore active gate", "if (at<uint8_t>(object, 0x68CF9) == 0)", "if (false)"),
        ("retain pending counter", "at<uint32_t>(object, 0x68CF4) = 0;", "at<uint32_t>(object, 0x68CF4) = 1;"),
        ("reset only first record", "i < at<int32_t>(queue, 0x08)", "i < 1 && i < at<int32_t>(queue, 0x08)"),
        ("lose minus-one sentinel", "i * 0x14 + 0x0C) = -1", "i * 0x14 + 0x0C) = 0"),
        ("wrong queue reset cursor", "0x18) = at<uint32_t>(queue, 0x10)", "0x18) = at<uint32_t>(queue, 0x14)"),
        ("clear slot payload", "at<uint32_t>(entries, i * 8) = 0;", "at<uint32_t>(entries, i * 8 + 4) = 0;"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/player/player_serve_callbacks.cpp").read_text()
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
