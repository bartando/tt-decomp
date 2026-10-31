"""Only behavioral FAIL counts for the former texture-release stub."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("skip decrement", "references = static_cast<uint16_t>(references - 1u);", "/* lost decrement */"),
    ("wrong reference field", "+ 6);", "+ 4);"),
    ("premature release", "if (references == 0)", "if (references <= 1)"),
    ("omit delete flag", "texture->destructor(true);", "texture->destructor(false);"),
    ("wrong virtual", "texture->destructor(true);", "texture->vfn_1();"),
    ("return modified dead count", "return 0;", "return references;"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/graphics/texture_reference.cpp").read_text()
    start = source.index("uint32_t Release(grcTexture* texture) {")
    body = source[start:source.index("\n}", start) + 2]
    for label, old, new in CASES:
        assert body.count(old) == 1, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("texture_release.py"),
                         Options(seed=1, patches=((body, body.replace(old, new)),))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if caught else 'MISSED'} {label}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
