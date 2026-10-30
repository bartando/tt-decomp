"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_grc_device_set_render_target_mutations.py

Only mutates build-cache copies of SetRenderTarget, never the working source.
Only behavioral FAIL (exit 1) counts; build/spec/emulator errors are failures
of this runner, not evidence that a mutation was caught.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    # The fence stamp, reference unit and release test live in the shared
    # dropDeviceReference; grc_device_set_indices mutates those.
    ("acquire before releasing the same surface", "    dropDeviceReference(state, previous);",
     "    if (surface != nullptr) static_cast<uint32_t*>(surface)[0] += kDeviceReference;\n"
     "    dropDeviceReference(state, previous);"),
    ("omit the new reference", "header[0] += kDeviceReference;", ""),
    ("collapse the colour register gap", "slot == 0 ? 0 : slot + 1u", "slot"),
    ("copy the wrong surface word", "field(colorOffset) = header[13];",
     "field(colorOffset) = header[12];"),
    ("omit colour-info dirty bit", "dirty |= dirtyBit;", ""),
    ("skip format 12 conversion", " || format == 12", ""),
    ("wrap oversized format shifts", "formatShift < 32 ? 2u << formatShift : 0",
     "2u << (formatShift & 31u)"),
    ("invert the format mode selection", "const uint32_t modeMask = mode - 1u;",
     "const uint32_t modeMask = ~(mode - 1u);"),
    ("leave the surface format unchanged",
     "header[13] = (header[13] & ~0x000F0000u) | formatBits;", ""),
    ("omit depth-only target-size callback", "if (sizeSurface != nullptr)",
     "if (surface != nullptr)"),
    ("ignore the fifth tiled target", "tiled && i < 5", "tiled && i < 4"),
    ("ignore the explicit bin mask", "field(12960) == 0 && ", ""),
    ("keep write mask on unbind",
     "field(12536 + slot * 4u) != 0 ? field(11956 + slot * 4u) : 0",
     "field(11956 + slot * 4u)"),
    ("omit colour-write dirty flag",
     "*reinterpret_cast<uint64_t*>(state + 40) |= UINT64_C(0x0800000000000000);", ""),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/graphics/grc_device.cpp").read_text()
    begin = source.index('extern "C" void grcDevice_SetRenderTarget(')
    end = source.index('\n// Bind `texture`', begin)
    function = source[begin:end]
    spec = Path(__file__).with_name("grc_device_set_render_target.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert old in function, f"mutation anchor changed: {name}"
        mutant = function.replace(old, new)
        if name == "acquire before releasing the same surface":
            mutant = mutant.replace("        header[0] += kDeviceReference;", "")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((function, mutant),))).run()
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
