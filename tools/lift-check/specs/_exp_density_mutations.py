"""Exact exponential reduction/scaling and Gaussian argument/normalization proof."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = [
    ('crt_exp', 'src/crt/exp.cpp', 'double roundExpExponent(', [
        ('skip exponent rounding', 'return shifted - bias;', 'return scaled;'),
    ]),
    ('crt_exp', 'src/crt/exp.cpp', 'double crt_exp(', [
        ('wrong inverse logarithm', 'value * 0x1.71547652b8ecbp+0', 'value'),
        ('wrong reduction sign', '-__builtin_fma(exponent, 0x1.62e42fefa39efp-1, -value)', '__builtin_fma(exponent, 0x1.62e42fefa39efp-1, -value)'),
        ('wrong numerator coefficient', 'square, 0.25)', 'square, 0.5)'),
        ('wrong rational denominator', 'denominator - numerator', 'denominator + numerator'),
        ('forget exponent scaling', 'if (adjustment != 0)', 'if (false)'),
        ('wrong exponent shift', '(oldExponent + adjustment) << 4', '(oldExponent + adjustment) << 3'),
        ('exclusive overflow cutoff', 'highDifference >= 0.0', 'highDifference > 0.0'),
        ('exclusive zero cutoff', 'lowDifference >= 0.0', 'lowDifference > 0.0'),
        ('ignore overflow replacement', 'result = g_crtExpOverflow;', 'result = __builtin_inf();'),
    ]),
    ('normal_density', 'src/rage/math/normal_density.cpp', 'float normalDensity(', [
        ('wrong normalization constant', 'variance * 0x1.921fb6p+2f', 'variance * 3.0f'),
        ('wrong variance factor', 'variance * 2.0f', 'variance * 3.0f'),
        ('wrong exponent sign', 'crt_exp(-ratio)', 'crt_exp(ratio)'),
        ('wrong reciprocal', '1.0f / normalization', 'normalization'),
        ('drop decay', 'return inverseNormalization * decay;', 'return inverseNormalization;'),
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
