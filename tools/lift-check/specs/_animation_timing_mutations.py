"""Require behavioral FAILs for animation evaluation/envelope regressions."""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ('animation_evaluate_2858', 'float LocomotionStateAnim_2858(', [
        ('empty evaluation', '    void* clip', '    return 0.0f;\n    void* clip'),
        ('omit duration', 'timingField<float>(clip, 0x0C) * timingField<float>(entry, 0x14)',
         'timingField<float>(entry, 0x14)'),
        ('wrong phase offset', 'timingField<float>(entry, 0x14);\n    LocomotionStateAnim_88E0_g',
         'timingField<float>(entry, 0x04);\n    LocomotionStateAnim_88E0_g'),
        ('wrong evaluator flags', 'frame, frame, 0, 1, time', 'frame, frame, 1, 0, time'),
        ('omit clip evaluation', 'LocomotionStateAnim_88E0_g(clip, frame, frame, 0, 1, time);', '(void)time;'),
        ('omit phase advance', 'LocomotionStateAnim_28B0_w(entry);', '(void)entry;'),
        ('return evaluation time', 'return timingField<float>(entry, 0x14)', 'return time'),
    ]),
    ('animation_blend_factor', 'float LocomotionStateAnim::CalculateBlendFactor(', [
        ('empty envelope', '    float phase', '    return 0.0f;\n    float phase'),
        ('old zero-phase error', 'if (phase == zero) phase = one', 'if (phase == one) phase = zero'),
        ('skip zero-phase substitution', 'if (phase == zero) phase = one;', '(void)zero;'),
        ('omit descending half', 'phase >= one - blendOut', 'false'),
        ('wrong descending width', 'width = blendOut', 'width = one - blendOut'),
        ('wrong descending numerator', 'phase = one - phase', 'phase = phase - one'),
        ('wrong saturation result', 'if (phase >= width) return one', 'if (phase >= width) return zero'),
        ('old late branch', '!(phase <= zero)', 'phase > one'),
        ('omit unordered division', '!(phase <= zero)', 'phase > zero'),
        ('return numerator', 'return phase / width', 'return phase'),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/anim/animation_timing.cpp').read_text()
    count = 0
    for spec, signature, mutations in CASES:
        start = source.index('\n' + signature) + 1
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, label
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + '.py'),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f'MISSED {label}: BUILD {exc}', flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and 'faulted' not in report
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: " +
                  (report.splitlines()[0] if report else 'no checker output'), flush=True)
            if not caught:
                print(report)
                return 1
            count += 1
    print(f'Caught {count}/{count} mutations', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
