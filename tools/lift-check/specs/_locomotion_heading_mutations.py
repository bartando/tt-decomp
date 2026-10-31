"""Prove sector, callback sequencing, geometry and blend-weight observations."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/anim/locomotion_heading.cpp'
CASES = [
    ('locomotion_clamp_heading', 'float clampCoordinate(', [
        ('skip lower clamp', 'difference >= 0.0f ? value : low', 'value'),
        ('skip upper clamp', 'upperDifference >= 0.0 ? high : lowerClamped', 'lowerClamped'),
    ]),
    ('locomotion_clamp_heading', 'float ramp(', [
        ('skip zero clamp', '-value >= 0.0f ? 0.0f : value', 'value'),
        ('wrong ramp denominator', 'end - start', 'end'),
    ]),
    ('locomotion_clamp_heading', 'const float* rangeFor(', [
        ('wrong entry index', '*reinterpret_cast<int32_t*>(bytes + 0x1c)', '0'),
        ('wrong entry stride', '* 68', '* 64'),
    ]),
    ('locomotion_clamp_heading', 'float LocomotionStateAnim_ClampHeading(', [
        ('test full bounds result', '(ops->GetBounds(&lower, &upper) & 0xffu)', 'ops->GetBounds(&lower, &upper)'),
        ('wrong front sector edge', 'magnitude <= kQuarterPi', 'magnitude < kQuarterPi'),
        ('wrong rear sector edge', 'magnitude >= kThreeQuarterPi', 'magnitude > kThreeQuarterPi'),
        ('wrong nearest X side', 'lowDistance < highDistance;', 'lowDistance > highDistance;'),
        ('test full side result', '(ops->IsForwardSide() & 0xffu)', 'ops->IsForwardSide()'),
        ('reverse side orientation', 'forward ? magnitude < kHalfPi : magnitude > kHalfPi', 'forward ? magnitude > kHalfPi : magnitude < kHalfPi'),
        ('wrong signed Z direction', 'forward ? heading > 0.0f : heading < 0.0f', 'forward ? heading < 0.0f : heading > 0.0f'),
        ('forget rear wrap', 'return LocomotionStateAnim_WrapAngle(adjusted);', 'return adjusted;'),
        ('reload range after side callback', 'const float scale = ramp(distance, start, end);', 'const float scale = ramp(distance, range[0], range[1]);'),
    ]),
    ('locomotion_blend_weight', 'float LocomotionStateAnim_6DD8_w(', [
        ('skip heading dispatch', '(void)LocomotionStateAnim_ClampHeading(state, heading);', '(void)heading;'),
        ('read stale table', 'const float* range = rangeFor(state);', 'const float* range = reinterpret_cast<const float*>(rage::load_ptr32<uint8_t>(state, 0x154) + *reinterpret_cast<int32_t*>(static_cast<uint8_t*>(state) + 0x150) * 68 + 0x38);'),
        ('swap blend range', 'const float start = range[0], end = range[1];', 'const float start = range[1], end = range[0];'),
        ('drop blend cap', 'difference >= 0.0f ? maxWeight : blend', 'blend'),
        ('ignore mutable offset', 'g_blendCurveOffset)', '0.01f)'),
    ]),
]


def main():
    total = 0
    for spec, signature, mutations in CASES:
        source = (ROOT / SOURCE).read_text()
        start = source.index(signature)
        body = source[start:source.index('\n}', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) >= 1, (spec, name, body.count(old))
            mutant = body.replace(old, new, 1)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                    Options(trials=300, seed=1, patches=((body, mutant),))).run()
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
