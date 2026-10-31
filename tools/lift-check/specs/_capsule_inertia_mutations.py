"""Behavioral mutations for capsule inertia and both hidden-result wrappers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = [
    ('ph_capsule_inertia', 'src/physics/ph_update_object.cpp', 'void phCapsule_ComputeInertia(', [
        ('restore zero stub', 'output[0] = transverse;', 'output[0] = 0.0f;'),
        ('omit axial mass', 'normalizedAxial * mass', 'normalizedAxial'),
        ('omit transverse mass', 'normalizedTransverse * mass', 'normalizedTransverse'),
        ('wrong denominator', '__builtin_fmaf(radius, g_capsuleVolK1, length)', '__builtin_fmaf(length, g_capsuleVolK1, radius)'),
        ('unfuse radial term', '__builtin_fmaf(radiusCubed, g_capsuleInertiaRadialK,\n                                            lengthSquaredRadius)', '(radiusCubed * g_capsuleInertiaRadialK + lengthSquaredRadius)'),
        ('wrong axial scale', 'axialMass * g_phTwo', 'axialMass * g_capsuleInertiaThird'),
        ('wrong transverse scale', 'transverseMass * g_capsuleInertiaThird', 'transverseMass * g_phTwo'),
        ('wrong Z axis', 'output[2] = transverse;', 'output[2] = axialMass;'),
    ]),
    ('ph_bound_capsule_inertia', 'src/physics/ph_physics.cpp', 'rage::phInertiaDiagonal rage::phBoundCapsule::ComputeInertia(', [
        ('wrong radius field', 'shape + 0x70', 'shape + 0x80'),
        ('wrong length field', 'shape + 0x80', 'shape + 0x90'),
        ('omit mass', 'result.xyz, mass, radius, length', 'result.xyz, 1.0f, radius, length'),
    ]),
    ('ph_bound_tapered_capsule_inertia', 'src/physics/ph_physics.cpp', 'phInertiaDiagonal phBoundTaperedCapsule::ComputeInertia(', [
        ('wrong radius field', 'shape + 0x70', 'shape + 0x80'),
        ('wrong length field', 'shape + 0x90', 'shape + 0x80'),
        ('swap geometry arguments', 'result.xyz, mass, radius, length', 'result.xyz, mass, length, radius'),
    ]),
]


def main():
    total = 0
    for spec, path, signature, mutations in CASES:
        source = (ROOT / path).read_text()
        start = source.index(signature)
        body = source[start:source.index('\n}\n', start) + 2]
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
