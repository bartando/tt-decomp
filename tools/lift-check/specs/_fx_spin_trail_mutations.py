"""Run with the lift-check venv and PYTHONPATH=tools/lift-check.

Compile mutated copies in the build cache; never modify the checked-in lift.
Only behavioral FAIL counts as detection, not BUILD/SPEC/UNSUPPORTED errors.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/graphics/fx_effects.cpp").read_text()
    source = source.replace('"fx_effects.hpp"', '"graphics/fx_effects.hpp"')
    source = source.replace('"../rage/memory.hpp"', '"rage/memory.hpp"')
    include = '#include "../../../src/graphics/fx_effects.cpp"'
    spec = Path(__file__).with_name("fx_spin_trail.py")
    mutations = [
        ("batch vertex count", "rage_2A78(6, 124);", "rage_2A78(6, 120);"),
        ("missing final sample", "step < kSpinSamplesPerPass; ++step", "step < kSpinSamplesPerPass - 1; ++step"),
        ("wrong axis argument", "rotation, &spinAxis.x, angle", "rotation, &color.x, angle"),
        ("reversed sweep", "const float angle = t * 1.75f;", "const float angle = t * -1.75f;"),
        ("transposed rotation", "rotation[row * 4 + lane]", "rotation[lane * 4 + row]"),
        ("wrong transform row", "fxSpinVectorFloat(matrix[4 + row])", "fxSpinVectorFloat(matrix[row])"),
        ("missing radius", "rotated * fxSpinVectorFloat(radius)", "rotated"),
        ("reversed height test", "position[2] < height", "position[2] > height"),
        ("wrong height stride", "g_phFrameCounter << 6", "g_phFrameCounter << 5"),
        ("missing taper absolute value", "1.0f - __builtin_fabsf(t)", "1.0f - t"),
        ("missing VMX flush", "if ((bits & 0x7f800000u) == 0)", "if (false)"),
        ("missing device restore", "field<uint32_t>(g_binkVideoPlayer, 0) = field<uint32_t>(g_binkVideoPlayer, 13652);", "(void)g_binkVideoPlayer;"),
    ]
    for name, old, new in mutations:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=64, seed=1,
                         patches=((include, source.replace(old, new, 1)),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"fx_spin_trail: caught {len(mutations)}/{len(mutations)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
