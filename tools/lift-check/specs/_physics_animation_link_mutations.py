"""Behavioral mutations for look-at dispatch, relocation, projected correction and sphere bounds."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
PHYSICS = 'src/physics/ph_physics.cpp'
CASES = [
    ('look_at_set_target', 'src/anim/look_at_controller.cpp', 'void game_28F0(', [
        ('wrong return mask', '& 0xffu', '& 0xffffffffu'),
        ('wrong selector', 'SetTarget(target, which)', 'SetTarget(target, 0)'),
        ('skip virtual gate', '->IsEnabled() & 0xffu', '->IsEnabled() & 0u'),
    ]),
    ('look_at_save_target', 'src/anim/look_at_controller.cpp', 'void game_2A40(', [
        ('wrong saved target', '+ 0x10', '+ 0x20'),
        ('wrong return mask', '& 0xffu', '& 0xffffffffu'),
    ]),
    ('ph_vector_accumulate_projected', 'src/physics/collider_velocity.cpp', 'void phVector_AccumulateProjected(', [
        ('include W in dot', 'dot3(old, increment)', 'dot3(old, increment) + old[3] * increment[3]'),
        ('omit projection', 'g_floatOne - fraction', 'g_floatOne'),
        ('unordered write', 'if (!(magnitudeSquared > projection)) return;', 'if (magnitudeSquared <= projection) return;'),
        ('leave W', 'std::memcpy(current, result, 16);', 'std::memcpy(current, result, 12);'),
    ]),
    ('ph_collider_accumulate_correction', PHYSICS, 'void rage::phArticulatedCollider::DelegateToBoundCapsule(', [
        ('wrong embedded field', '+ 0x160', '+ 0x170'),
    ]),
    ('ph_advance_segmented_pointer', PHYSICS, 'void ph_AdvanceSegmentedPtr(', [
        ('wrong table entry', 'words[index + 2]', 'words[index + 3]'),
        ('skip relocation', '*slot = current + adjustment;', '*slot = current;'),
        ('reverse adjustment', '*slot = current + adjustment;', '*slot = current - adjustment;'),
    ]),
    ('ph_sphere_rebuild_bounds', PHYSICS, 'void phSphere_RebuildBounds(', [
        ('wrong center flag', 'bytes[5]', 'bytes[6]'),
        ('wrong minimum sign', 'const float negativeRadius = -radius;', 'const float negativeRadius = radius;'),
        ('wrong radius slot', 'values[3] = radius + length;', 'values[2] = radius + length;'),
        ('wrong sentinel selection', 'estimate == phFlushVmx', 'estimate != phFlushVmx'),
        ('wrong root product', 'phFlushVmx(squaredLength) * refined', 'phFlushVmx(squaredLength) + refined'),
    ]),
]


def main():
    total = 0
    for spec, path, signature, mutations in CASES:
        source = (ROOT / path).read_text()
        start = source.index(signature)
        # Skip a forward declaration before searching for the definition.
        if ';' in source[start:source.index('{', start)]:
            start = source.index(signature, start + len(signature))
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
