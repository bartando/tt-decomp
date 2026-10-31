"""Scalar conjugate products and relative-transform call/payload observations."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/rage/math/quat_ops.cpp'
CASES = [
    ('quat_multiply_conjugate', 'void quatMultiplyConjugate(', [
        ('wrong dot seed', 'left[2] * right[2]', 'left[2] * right[1]'),
        ('wrong W sign', 'out[3] = __builtin_fmaf(right[3], left[3], xyz);', 'out[3] = __builtin_fmaf(-right[3], left[3], xyz);'),
        ('wrong scalar product sign', 'right[3], -product', 'right[3], product'),
        ('wrong cross sign', 'const float cross = -__builtin_fmaf', 'const float cross = __builtin_fmaf'),
        ('omit Z store', 'axis < 3', 'axis < 2'),
    ]),
    ('locomotion_relative_transform', 'void* LocomotionStateAnim_BE20_g(', [
        ('invert left quaternion', 'result[axis] = -b[axis]', 'result[axis] = -a[axis]'),
        ('wrong right translation', 'util_BBB0(result, b + 4, result + 4);', 'util_BBB0(result, a + 4, result + 4);'),
        ('omit inverse translation', 'flushRelativeVmx(lbl_82606750[lane]) - flushRelativeVmx(result[4 + lane])', 'flushRelativeVmx(result[4 + lane])'),
        ('wrong second rotation', 'util_BBB0(a, inverseTranslation, result + 4);', 'util_BBB0(b, inverseTranslation, result + 4);'),
        ('add wrong origin', 'flushRelativeVmx(a[4 + lane])', 'flushRelativeVmx(b[4 + lane])'),
        ('reverse conjugate product', 'rage::quatMultiplyConjugate(result, a, b);', 'rage::quatMultiplyConjugate(result, b, a);'),
    ]),
]


def main():
    total = 0
    for spec, signature, mutations in CASES:
        source = (ROOT / SOURCE).read_text()
        start = source.index(signature)
        body = source[start:source.index('\n}', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) == 1, (spec, name, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                    Options(trials=100, seed=1, patches=((body, body.replace(old, new)),))).run()
            report = output.getvalue()
            caught = rc == 1 and 'FAIL' in report and 'the lift faulted' not in report
            print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f'Caught {total}/{total} mutations', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
