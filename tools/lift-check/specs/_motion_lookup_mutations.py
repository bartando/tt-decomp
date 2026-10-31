"""Root-motion and bone-copy specs must reject behavioral cache-only mutants."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("root_motion_blend", "src/anim/root_motion_blend.cpp", [
        ("overwrite w on failure", "output->x = output->y = output->z = 0.0f;", "output->x = output->y = output->z = output->_pad = 0.0f;"),
        ("wrong reversal", "if (start > end)", "if (start < end)"),
        ("lose reversed w", "subtractVmx(lbl_82606750[3], reversed._pad)", "0.0f"),
        ("ignore low-byte status", "static_cast<uint8_t>(result)", "result"),
        ("wrong sample delta", "const float delta = end - start;", "const float delta = end;"),
        ("wrong absolute sample time", "duration * end, delta * duration", "end, delta * duration"),
        ("use rotation channels", "*output = sampled.translation;", "*output = sampled.rotation;"),
        ("ignore blend weight", "flushVmx(delta) * flushVmx(weight)", "flushVmx(delta) * 1.0f"),
        ("lose output return", "return output;", "return nullptr;"),
    ]),
    ("bone_matrix_lookup", "src/anim/bone_matrix_lookup.cpp", [
        ("wrong bone id", "at<uint16_t>(bone, 0x40)", "0"),
        ("wrong matrix stride", "uint32_t(index) * 64", "uint32_t(index) * 16"),
        ("drop fourth row", "at<MatrixRow>(output, 0x30) = at<MatrixRow>(source, 0x30);", "(void)source;"),
        ("copy wrong second row", "at<MatrixRow>(output, 0x10) = at<MatrixRow>(source, 0x10);", "at<MatrixRow>(output, 0x10) = at<MatrixRow>(source, 0);"),
        ("write on lookup failure", "rage_debugLog(g_boneMatrixLookupFailed);", "at<uint32_t>(output, 0) = 0; rage_debugLog(g_boneMatrixLookupFailed);"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    count = 0
    for spec, path, mutations in CASES:
        source = (root / path).read_text()
        for label, old, new in mutations:
            assert old in source, f"missing mutation anchor: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
