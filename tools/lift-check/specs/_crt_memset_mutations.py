"""Run with PYTHONPATH=tools/lift-check and the lift-check venv's Python."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("write even when count is zero", "if (count == 0)\n        return dst;",
     "if (count == 0) { *p = v; return dst; }"),
    ("return the wrong address", "    return dst;\n}",
     "    return (unsigned char*)dst + 1;\n}"),
    ("use the wrong alignment byte", "        *p++ = v;\n        --count;",
     "        *p++ = v ^ 1;\n        --count;"),
    ("lose high bytes in bulk word", "word          |= word << 16;",
     "word          |= word << 8;"),
    ("skip final word of each bulk block", "            pw[3] = word;",
     "            /* missing pw[3] */"),
    ("skip the final tail byte", "while (count--)\n        *p++ = v;",
     "while (count > 1) { --count; *p++ = v; }"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/crt/memory.c").read_text()
    target, after = source.split("\n\n/**\n * memmove @", 1)
    for name, old, new in MUTATIONS:
        assert target.count(old) == 1, name
        mutated = target.replace(old, new) + "\n\n/**\n * memmove @" + after
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("crt_memset.py"),
                         Options(seed=1, patches=((source, mutated),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}",
              flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
