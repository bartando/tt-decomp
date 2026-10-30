"""Run from the repo root:

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_crt_memcpy_mutations.py

Mutate build-cache copies only. Run the default sample as the baseline and for
every mutation. Only behavioral FAIL (1) counts as a caught mutation, never
BUILD, SPEC, UNSUPPORTED or an exception. Full seed runs are separate.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options, load_spec


SPEC = Path(__file__).with_name("crt_memcpy.py")
TAIL = "    while (count--)\n        *d++ = *s++;\n    return dst;"
MUTATIONS = (
    ("write on zero count",
     "    size_t headBytes = (8 - ((uintptr_t)d & 7)) & 7;",
     "    if (count == 0) { *d = 0; return dst; }\n"
     "    size_t headBytes = (8 - ((uintptr_t)d & 7)) & 7;",
     (0, 0, 0, False)),
    ("return advanced destination", TAIL, TAIL.replace("return dst;", "return d;"),
     (1, 0, 1, False)),
    ("return source", TAIL, TAIL.replace("return dst;", "return (void*)src;"),
     (1, 0, 1, False)),
    ("skip destination alignment bytes",
     "    count -= headBytes;\n    while (headBytes--)",
     "    count -= headBytes;\n    d += headBytes; s += headBytes; headBytes = 0;\n"
     "    while (headBytes--)",
     (8, 1, 0, False)),
    ("omit doubleword tail store",
     "        while (count >= 8) {\n            *(uint64_t*)d = *(const uint64_t*)s;",
     "        while (count >= 8) {\n            (void)s;",
     (8, 0, 0, False)),
    ("omit word tail store",
     "        while (count >= 4) {\n            *(uint32_t*)d = *(const uint32_t*)s;",
     "        while (count >= 4) {\n            (void)s;",
     (4, 0, 4, False)),
    ("omit byte tail", TAIL, "    return dst;",
     (1, 0, 1, False)),
    ("omit last word in bulk group", "                    dw[3] = last;",
     "                    (void)last;",
     (256, 0, 4, False)),
    ("preload fourth word before first store",
     "                    dw[0] = a;\n                    uint32_t last = sw[3];",
     "                    uint32_t last = sw[3];\n                    dw[0] = a;",
     (255, 12, 0, True)),
    ("truncate gathered bulk loop", "for (size_t i = 0; i < 32; ++i)",
     "for (size_t i = 0; i < 31; ++i)",
     (256, 0, 1, False)),
    ("lose doubleword pipeline on overlap",
     "                    uint64_t c = sq[i + 2];\n"
     "                    dq[i] = a;\n                    a = b;\n                    b = c;\n"
     "                }\n                dq[14] = a;\n                dq[15] = b;",
     "                    dq[i] = sq[i];\n"
     "                }\n                dq[14] = sq[14];\n                dq[15] = sq[15];",
     (255, 21, 13, True)),
    ("copy gathered words byte by byte on overlap",
     "                *(uint32_t*)d = gathered.word;",
     "                for (size_t byte = 0; byte < 4; ++byte) d[byte] = s[byte];",
     (255, 12, 11, True)),
    ("use memmove behavior on backward overlap",
     "    size_t sourceAlignment = (uintptr_t)s & 7;",
     "    if ((uintptr_t)d > (uintptr_t)s && (uintptr_t)d - (uintptr_t)s < count) {\n"
     "        while (count--) d[count] = s[count];\n        return dst;\n    }\n"
     "    size_t sourceAlignment = (uintptr_t)s & 7;",
     (255, 12, 11, True)),
)


def main():
    spec = load_spec(SPEC)
    root = SPEC.resolve().parents[3]
    source = (root / spec.SOURCE).read_text()
    start = source.index("void* memcpy(void* dst, const void* src, size_t count)\n{")
    function = source[start:]
    assert not spec.FULL, "run mutations without LIFTCHECK_MEMCPY_FULL=1"
    cases = {spec.case(index) for index in range(spec.TRIALS)}
    assert all(case in cases for _, _, _, case in MUTATIONS), "sample lost a mutation witness"
    if Checker(SPEC, Options(seed=1)).run() != 0:
        return 1
    for name, old, new, _ in MUTATIONS:
        assert function.count(old) == 1, f"mutation anchor changed: {name}"
        patch = (function, function.replace(old, new, 1))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(SPEC, Options(seed=1, patches=(patch,))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
