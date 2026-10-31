"""Require behavioral failures for the corrected LOD forwarding signature."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("wrong getter", "GetTexture2()", "GetTexture()"),
    ("truncate level", "texture->SetLodLevel(level);", "texture->SetLodLevel(level & 255);"),
    ("wrong method", "texture->SetLodLevel(level);", "texture->vfn_15();"),
    ("lose null guard", "if (texture)", "if (true)"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/graphics/texture_reference.cpp").read_text()
    start = source.index("void rage::grcTextureReferenceBase::ForwardSlot16(uint32_t level)")
    body = source[start:source.index("\n}", start) + 2]
    for label, old, new in CASES:
        assert body.count(old) == 1, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("texture_reference_lod_level.py"),
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
