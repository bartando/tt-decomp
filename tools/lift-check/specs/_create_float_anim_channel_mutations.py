"""Run with PYTHONPATH=tools/lift-check and its venv Python from repo root.

Patches build copies only; every mutant must compile and report FAIL (1).
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("wrong static encoding", "constant->m_encoding = 4;", "constant->m_encoding = 3;"),
    ("wrong quantized encoding", "quantized->m_encoding = 6;", "quantized->m_encoding = 5;"),
    ("wrong raw encoding", "raw->m_encoding = 1;", "raw->m_encoding = 2;"),
    ("uninitialized quantized samples", "quantized->samples = nullptr;", "/* omitted */"),
    ("uninitialized raw capacity", "raw->capacity = 0;", "/* omitted */"),
    ("wrong static allocation", "allocate(allocator, 12, 16)", "allocate(allocator, 16, 16)"),
    ("wrong quantized allocation", "::rage_Alloc(24)", "::rage_Alloc(20)"),
    ("wrong raw allocation", "::rage_Alloc(16)", "::rage_Alloc(12)"),
    ("test full static status",
     "static_cast<uint8_t>(initialize(constant, samples, sampleCount, skip, tolerance))",
     "initialize(constant, samples, sampleCount, skip, tolerance)"),
    ("test full quantized status",
     "static_cast<uint8_t>(initialize(quantized, samples, sampleCount, skip, tolerance))",
     "initialize(quantized, samples, sampleCount, skip, tolerance)"),
    ("wrong sample stride", "initialize(quantized, samples, sampleCount, skip, tolerance)",
     "initialize(quantized, samples, sampleCount, skip + 1, tolerance)"),
    ("lose tolerance", "initialize(constant, samples, sampleCount, skip, tolerance)",
     "initialize(constant, samples, sampleCount, skip, 0.0f)"),
    ("quantized wins ties", "if (quantizedSize < rawSize)", "if (quantizedSize <= rawSize)"),
    ("unsigned size comparison", "int32_t quantizedSize =", "uint32_t quantizedSize ="),
    ("wrong delete flag", "(raw->vtable[0])(raw, 1);", "(raw->vtable[0])(raw, 0);"),
    ("delete the winning candidate", "(raw->vtable[0])(raw, 1);",
     "(quantized->vtable[0])(quantized, 1);"),
    ("omit raw initialization",
     "reinterpret_cast<InitializeFn>(raw->vtable[8])(raw, samples, sampleCount, skip, tolerance);",
     "/* omitted raw initialization */"),
    ("leak failed static candidate",
     "reinterpret_cast<DestroyFn>(constant->vtable[0])(constant, 1);", "/* omitted destruction */"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/animation/rage_anim.cpp").read_text()
    spec = Path(__file__).with_name("create_float_anim_channel.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
        print(f'{"CAUGHT" if rc == 1 else "MISSED"} {name}: '
              f'{output.getvalue().splitlines()[0]}', flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
