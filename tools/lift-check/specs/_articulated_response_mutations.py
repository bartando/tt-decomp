"""Behavioral proof for single-body impulses, response columns and matrix/caller ABI."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/physics/ph_physics.cpp'
CASES = [
    ('ph_articulated_point_impulse_response', 'void phArticulatedCollider_ApplyPointImpulseResponse(', [
        ('reverse point torque', '-(second - first)', 'second - first'),
        ('wrong inertia block', 'body + 0x310 / 4', 'body + 0x350 / 4'),
    ]),
    ('ph_articulated_angular_impulse_response', 'void phArticulatedCollider_ApplyAngularImpulseResponse(', [
        ('drop torque', 'memcpy(impulse + 4, torque, 16);', 'memset(impulse + 4, 0, 16);'),
    ]),
    ('ph_articulated_point_impulse_response', 'float* phSelectedResponse(', [
        ('wrong column stride', '* 32', '* 16'),
    ]),
    ('ph_articulated_point_impulse_response', 'void phPropagateSelectedResponse(', [
        ('mark all edges visited', 'data[105 + child] = 0;', 'data[105 + child] = 1;'),
        ('skip last ancestor', 'while (child > 0)', 'while (child > 1)'),
        ('wrong parent virtual', 'joint->ResolveParentResponse(', 'joint->ResolveChildResponse('),
        ('leave path unmarked', 'data[105 + child] = 1;', 'data[105 + child] = 0;'),
        ('reverse branch filter', 'data[105 + edge] != 0', 'data[105 + edge] == 0'),
        ('reverse forward response', 'joint->ResolveChildResponse(phSelectedResponse(parent), phSelectedResponse(destination));',
         'joint->ResolveChildResponse(phSelectedResponse(destination), phSelectedResponse(parent));'),
    ]),
    ('ph_articulated_build_point_response', 'void phArticulatedCollider_BuildPointResponse(', [
        ('skip last column', 'axis < 3', 'axis < 2'),
        ('always use first column', '= axis;', '= 0;'),
        ('leave selectors dirty', '*rage::load_ptr32<uint32_t>(data, (10 + i) * 4) = 0;',
         '*rage::load_ptr32<uint32_t>(data, (10 + i) * 4) = 2;'),
    ]),
    ('ph_articulated_build_angular_response', 'void phArticulatedCollider_BuildAngularResponse(', [
        ('wrong unit torque', 'g_phResponseBasis[axis]', 'g_phResponseBasis[(axis + 1) % 3]'),
        ('skip last angular column', 'axis < 3', 'axis < 2'),
    ]),
    ('ph_articulated_point_response_matrix', 'void phArticulatedCollider_GetPointResponseMatrix(', [
        ('wrong skew sign', 'output[1] = -z;', 'output[1] = z;'),
        ('wrong angular columns', '(0x10 + column * 32)', '(0x20 + column * 32)'),
        ('wrong linear columns', '(0x20 + column * 32)', '(0x10 + column * 32)'),
        ('subtract linear response', 'phFlushVmx(output[i]) + phFlushVmx(linear[i])', 'phFlushVmx(output[i]) - phFlushVmx(linear[i])'),
        ('snapshot overlapping point', '    const float z = point[2], y = point[1];',
         '    float copy[3] = {point[0], point[1], point[2]};\n    point = copy;\n    const float z = point[2], y = point[1];'),
    ]),
    ('ph_articulated_point_response_matrix_caller', 'void rage::phArticulatedCollider::GetJointPointResponseMatrix(', [
        ('wrong alternate bone', 'alternateTarget ? alternateBoneIndex : boneIndex', 'boneIndex'),
        ('reverse relative point', 'phFlushVmx(point[lane]) - phFlushVmx(origin[lane])', 'phFlushVmx(origin[lane]) - phFlushVmx(point[lane])'),
        ('drop output pointer', 'bodyIndex, delta, output);', 'bodyIndex, delta, delta);'),
    ]),
    ('ph_articulated_build_point_response_caller', 'void rage::phArticulatedCollider::BuildJointPointResponse(', [
        ('drop bone index', 'phArticulatedCollider_E668(this, boneIndex)', 'phArticulatedCollider_E668(this, 0)'),
        ('reverse response point', 'phFlushVmx(point[lane]) - phFlushVmx(origin[lane])', 'phFlushVmx(origin[lane]) - phFlushVmx(point[lane])'),
    ]),
    ('ph_articulated_build_angular_response_caller', 'void rage::phArticulatedCollider::BuildJointAngularResponse(', [
        ('drop angular bone index', 'phArticulatedCollider_E668(this, boneIndex)', 'phArticulatedCollider_E668(this, 0)'),
    ]),
]


def main():
    source = (ROOT / SOURCE).read_text()
    total = 0
    for spec, signature, mutations in CASES:
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
