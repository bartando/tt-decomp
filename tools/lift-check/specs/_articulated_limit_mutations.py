"""Behavioral proof for constraint array gathering, sign bits and the native caller."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = [
    ('ph_articulated_gather_joint_limits', 'src/physics/articulated_constraints.cpp',
     'int32_t phArticulatedCollider_GatherJointLimits(', [
        ('reverse limit error', 'const float error = value - limit;', 'const float error = limit - value;'),
        ('replace bit signs with numeric signs', '(valueBits ^ errorBits) & 0x80000000u', 'value * error < 0.0f'),
        ('wrong reference value', 'value - reference;', 'limit - reference;'),
        ('wrong weight', 'weights[row] = weight;', 'weights[row] = value;'),
        ('store owner too late',
         '            jointIndices[row] = index;\n            uint32_t state;\n            float value, weight, limit, reference;\n            joint = reinterpret_cast<rage::phArticulatedJointOps*>(uintptr_t(data[42 + index]));\n            joint->GetConstraintState(axis, &state, &value, &weight, &limit, &reference);',
         '            uint32_t state;\n            float value, weight, limit, reference;\n            joint = reinterpret_cast<rage::phArticulatedJointOps*>(uintptr_t(data[42 + index]));\n            joint->GetConstraintState(axis, &state, &value, &weight, &limit, &reference);\n            jointIndices[row] = index;'),
        ('cache replaced joint', '            joint = reinterpret_cast<rage::phArticulatedJointOps*>(uintptr_t(data[42 + index]));', '            (void)data;'),
        ('reload cached outer bound', 'index < jointCount', 'index < static_cast<int32_t>(data[1] - 1)'),
        ('wrong owner index', 'jointIndices[row] = index;', 'jointIndices[row] = index + 1;'),
        ('wrong count return', 'return total;', 'return jointCount;'),
    ]),
    ('ph_articulated_update_joint_limits', 'src/physics/ph_physics.cpp',
     'void rage::phArticulatedCollider::UpdateJointConstraintErrors(', [
        ('drop dirty flag', 'collider[0x1D4] = 1;', 'collider[0x1D4] = 0;'),
        ('wrong count stored', '*reinterpret_cast<int32_t*>(collider + 0x1D8) = count;', '*reinterpret_cast<int32_t*>(collider + 0x1D8) = count + 1;'),
        ('wrong owner output', 'collider + 0x1DC', 'collider + 0x1E4'),
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
