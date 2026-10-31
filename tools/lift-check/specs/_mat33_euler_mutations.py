"""Mutation proof for both recovered Euler extraction conventions."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/rage/math/mat33_extract_euler.cpp'
CASES = [
    ('mat33_extract_euler_xyz', SOURCE, 'float angleOrZero(', [
        ('wrong zero gate', 'x == zero && y == zero', 'x == zero || y == zero'),
    ]),
    ('mat33_extract_euler_xyz', SOURCE, 'void mat33ToEuler(', [
        ('skip orthonormalization', 'mat33Orthonormalize(basis);', '(void)basis;'),
        ('reverse atan arguments', 'basis[1], basis[0]', 'basis[0], basis[1]'),
        ('wrong asin sign', 'crt_asin(-basis[2])', 'crt_asin(basis[2])'),
        ('write W instead of Z', 'angles[2] = z;', 'angles[3] = z;'),
    ]),
    ('mat33_extract_euler_zxy', SOURCE, 'void mat33ToEulerZXY(', [
        ('wrong Y row', 'basis[8], basis[10]', 'basis[6], basis[10]'),
        ('wrong asin sign', 'crt_asin(-basis[9])', 'crt_asin(basis[9])'),
        ('swap X output', 'angles[0] = x;', 'angles[0] = z;'),
    ]),
]


def main():
    total = 0
    for spec, path, signature, mutations in CASES:
        source = (ROOT / path).read_text()
        start = source.index(signature)
        body = source[start:source.index('\n}', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) == 1, (spec, name, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                    Options(trials=80, seed=1, patches=((body, body.replace(old, new)),))).run()
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
