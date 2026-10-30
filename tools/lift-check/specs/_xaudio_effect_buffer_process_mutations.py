"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python <this file>."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong active bit", "effect->active & 1", "effect->active & 2"),
    ("disabled returns failure", "return 0;\n\n    void* input", "return -1;\n\n    void* input"),
    ("wrong ping-pong mask", "(format & 6) == 6", "(format & 6) == 2"),
    ("skip pool lookup", "if (input == pool->buffers[index]) break;", "if (false) break;"),
    ("wrong match selection", "(index ^ 1)", "index"),
    ("wrong unknown selection", "(index ^ 1) : 0", "(index ^ 1) : 1"),
    ("fail to update current", "*current = output;", "/* omit current update */"),
    ("wrong input mask", "format & 3", "format & 1"),
    ("output as input", "output = *current;", "input = *current;"),
    ("wrong callback slot", "vtable[6]", "vtable[5]"),
    ("discard callback result", "return reinterpret_cast<Process>(vtable[6])(effect->interface, input, output);", "reinterpret_cast<Process>(vtable[6])(effect->interface, input, output); return 0;"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/audio/xaudio_effect_buffer.cpp").read_text()
    spec = Path(__file__).with_name("xaudio_effect_buffer_process.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, name
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {out.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(out.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
