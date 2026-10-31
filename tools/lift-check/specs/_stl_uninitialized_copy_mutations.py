"""Patch only cached function bodies; require behavioral FAILs, never faults.
Run with PYTHONPATH=tools/lift-check and tools/lift-check/.venv/bin/python.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("stl_uninitialized_copy_chars", "char* game_DD78_h(", [
        ("empty copy", "std::memcpy(dest, first, count);", "/* copy omitted */"),
        ("omit final byte", "std::memcpy(dest, first, count);", "std::memcpy(dest, first, count - 1);"),
        ("wrong end", "return dest + count;", "return dest;"),
    ]),
    ("stl_uninitialized_copy_matrix34", "Matrix34* fiAsciiTokenizer_DDD0_w(", [
        ("omit last row", "row < 4", "row < 3"),
        ("only first matrix", "        ++first;", "        first = last;"),
        ("wrong end", "    return dest;", "    return dest ? dest + 1 : dest;"),
        ("snapshot whole matrix", "            for (unsigned row = 0; row < 4; ++row) {\n                unsigned char bits[16];\n                std::memcpy(bits, reinterpret_cast<const unsigned char*>(first) + row * 16, 16);\n                std::memcpy(reinterpret_cast<unsigned char*>(dest) + row * 16, bits, 16);\n            }", "            unsigned char bits[64];\n            std::memcpy(bits, first, 64);\n            std::memcpy(dest, bits, 64);"),
    ]),
]

def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/io/fiAsciiTokenizer.cpp").read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, (spec, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            report = output.getvalue()
            caught = rc == 1 and "faulted" not in report
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f"Caught {total}/{total} behavioral mutations", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
