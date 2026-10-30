"""Run from the repo root with PYTHONPATH=tools/lift-check and .venv/bin/python.

Patch build-cache copies only; only behavioral FAIL counts as caught.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("OR instead of AND", "result[lane] = dirty[lane] & mask[lane];",
     "result[lane] = dirty[lane] | mask[lane];"),
    ("wrong inline mask", "instance + 128 + word * 8", "instance + 112 + word * 8"),
    ("wrong second mask", "self + 260);\n        filterGroup", "self + 256);\n        filterGroup"),
    ("skip first bank", "self + 288); word += 4)", "self + 288) && word != 0; word += 4)"),
    ("round down last group", "word < *reinterpret_cast<uint32_t*>(self + 288); word += 4)",
     "word + 4 <= *reinterpret_cast<uint32_t*>(self + 288); word += 4)"),
    ("upload before filtering", "    for (uint32_t word = 0; word < *reinterpret_cast<uint32_t*>(self + 288); word += 4)",
     "    rage_6370(self);\n    for (uint32_t word = 0; word < *reinterpret_cast<uint32_t*>(self + 288); word += 4)"),
    ("skip upload", "    rage_6370(self);\n}", "    (void)self;\n}"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/rage_grm.cpp").read_text()
    spec = Path(__file__).with_name("grm_shader_instance_filter_and_upload_parameters.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
