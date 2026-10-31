"""Reject incorrect axis polarity, dead zone and return behavior."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("pad_decode_axis", "ignore polarity", "bytes[3] ^ bytes[0]", "bytes[0]"),
    ("pad_decode_axis", "wrong center", "- 127.5f", "- 128.0f"),
    ("player_read_analog_axis", "wrong positive threshold", "> 0.25999999046325684f", "> 0.5f"),
    ("player_read_analog_axis", "wrong negative branch", "value + 0.25999999046325684f", "value - 0.25999999046325684f"),
    ("player_read_analog_axis", "lose float return", "return 0.0f;", "return 1.0f;"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/game/input/analog_axis.cpp").read_text()
    for spec, label, old, new in CASES:
        assert old in source, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
