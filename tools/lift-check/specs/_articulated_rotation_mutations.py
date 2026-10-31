"""Behavioral mutation proof for body/global angular displacement and its caller."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/physics/ph_physics.cpp'
CASES = [
    ('ph_articulated_body_rotate', 'void phArticulatedBody_Rotate(', [
        ('reverse threshold', '!(lengthSquared > g_phRotationMinSquared)', 'lengthSquared > g_phRotationMinSquared'),
        ('omit normalization', 'vector[lane]) * refined', 'vector[lane]) * 1.0f'),
        ('lose final transpose W', 'rage::mat33ComposeInPlace(basis, rotation);\n    memcpy(previous, basis, sizeof(previous));\n    for (unsigned row = 0; row < 3; ++row)\n        for (unsigned lane = 0; lane < 4;', 'rage::mat33ComposeInPlace(basis, rotation);\n    memcpy(previous, basis, sizeof(previous));\n    for (unsigned row = 0; row < 3; ++row)\n        for (unsigned lane = 0; lane < 3;'),
        ('omit final transpose', 'rage::mat33ComposeInPlace(basis, rotation);', 'rage::mat33ComposeInPlace(basis, rotation);\n    return;'),
        ('wrong angle', 'rotation, axis, length);', 'rotation, axis, lengthSquared);'),
    ]),
    ('ph_articulated_apply_angular_displacement', 'void phArticulatedCollider_ApplyAngularDisplacement(', [
        ('reverse displacement', '-(second - first)', 'second - first'),
        ('omit rotation', 'phArticulatedBody_Rotate(body, rotationVector);', '(void)body;'),
        ('wrong position field', 'body[0xC0 / 4 + lane] =', 'body[0xD0 / 4 + lane] ='),
        ('wrong angular cache', 'body + 0x130 / 4', 'body + 0x120 / 4'),
        ('reverse point correction', 'correction + point[lane]', 'point[lane] - correction'),
        ('unfuse correction', '__builtin_fmaf(angular[z], displacement[y], -product)', 'angular[z] * displacement[y] - product'),
    ]),
    ('ph_articulated_angular_displacement_caller', 'void rage::phArticulatedCollider::ApplyAngularDisplacement(', [
        ('omit dispatch', 'phArticulatedCollider_ApplyAngularDisplacement(\n        reinterpret_cast<void*>(uintptr_t(*reinterpret_cast<const uint32_t*>(\n            reinterpret_cast<const uint8_t*>(this) + 0x1D0))), rotationVector);', '(void)rotationVector;'),
    ]),
]


def main():
    source = (ROOT / SOURCE).read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        body = source[start:source.index('\n}\n', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) >= 1, (spec, name, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=100, seed=1, patches=((body, body.replace(old, new, 1)),))).run()
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
