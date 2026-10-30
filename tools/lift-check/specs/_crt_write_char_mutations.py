"""Run with PYTHONPATH=tools/lift-check and the lift-check venv's Python."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("ignore count-only mode", "if (!(stream->flags & 0x40) || stream->base)", "if (true)"),
    ("ignore non-null base", "if (!(stream->flags & 0x40) || stream->base)", "if (!(stream->flags & 0x40))"),
    ("decrement by two", "static_cast<uint32_t>(stream->remaining) - 1", "static_cast<uint32_t>(stream->remaining) - 2"),
    ("flush one byte early", "if (!(remaining & 0x80000000u))", "if (remaining != 0 && !(remaining & 0x80000000u))"),
    ("do not advance cursor", "*stream->cursor++", "*stream->cursor"),
    ("write wrong byte", "*stream->cursor++ = static_cast<unsigned char>(ch);", "*stream->cursor++ = static_cast<unsigned char>(ch + 1);"),
    ("flush unsigned character", "crtFlushChar(static_cast<int8_t>(ch), stream)", "crtFlushChar(static_cast<unsigned char>(ch), stream)"),
    ("ignore flush failure", "if (result == -1)", "if (false)"),
    ("increment by two", "static_cast<uint32_t>(*count) + 1", "static_cast<uint32_t>(*count) + 2"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/crt/printf.cpp").read_text()
    before, target = source.split('// @ 0x824347A0 | size: 0x94\n', 1)
    target, after = target.split('// @ 0x824348D0 | size: 0xB84\n', 1)
    caught = 0
    for name, old, new in MUTATIONS:
        assert target.count(old) == 1, name
        mutated = (before + '// @ 0x824347A0 | size: 0x94\n' + target.replace(old, new)
                   + '// @ 0x824348D0 | size: 0xB84\n' + after)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name('crt_write_char.py'),
                         Options(seed=1, patches=((source, mutated),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
