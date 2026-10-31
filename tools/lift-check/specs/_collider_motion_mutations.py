"""Behavioral mutation proof for collider motion and its articulated callers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CORE = 'src/physics/collider_velocity.cpp'
CALLER = 'src/physics/ph_physics.cpp'
CASES = [
    ('ph_collider_clamp_linear_speed', CORE, 'void clampSpeed(', [
        ('unordered clamp', 'if (!(speedSquared > limitSquared)) return;', 'if (speedSquared <= limitSquared) return;'),
        ('wrong scale', 'limit * reciprocal', 'reciprocal'),
        ('leave momentum', 'std::memcpy(momentum, scaled, 16);', '(void)momentum;'),
        ('leave W', 'std::memcpy(velocity, scaled, 16);', 'std::memcpy(velocity, scaled, 12);'),
    ]),
    ('ph_collider_clamp_angular_speed', CORE, 'void phCollider_ClampAngularSpeed(', [
        ('wrong limit', '0xf0, 0x110, 0x94', '0xf0, 0x110, 0x90'),
        ('wrong momentum', '0xf0, 0x110, 0x94', '0xf0, 0x100, 0x94'),
    ]),
    ('ph_collider_refresh_linear_velocity', CORE, 'void phCollider_RefreshLinearVelocity(', [
        ('wrong inverse mass', 'field(collider, 0x68)', 'field(collider, 0x64)'),
        ('skip notification', 'ops(collider)->OnLinearVelocityChanged();', '(void)collider;'),
        ('skip clamp', 'phCollider_ClampLinearSpeed(collider);', '(void)collider;'),
    ]),
    ('ph_collider_set_angular_velocity', CORE, 'void phCollider_SetAngularVelocity(', [
        ('wrong selector', 'GetInertia(inertia, 0)', 'GetInertia(inertia, 1)'),
        ('transpose', 'inertia[col], inertia[4 + col], inertia[8 + col]', 'inertia[col * 4], inertia[col * 4 + 1], inertia[col * 4 + 2]'),
        ('wrong W', 'momentum[3] = momentum[0];', 'momentum[3] = momentum[2];'),
    ]),
    ('ph_collider_refresh_angular_velocity', CORE, 'void phCollider_RefreshAngularVelocity(', [
        ('wrong diagonal', 'field(collider, 0x80)', 'field(collider, 0x70)'),
        ('wrong W', 'velocity[3] = velocity[0];', 'velocity[3] = velocity[2];'),
        ('skip clamp', 'phCollider_ClampAngularSpeed(collider);', '(void)collider;'),
    ]),
    ('ph_collider_reset', CORE, 'void phCollider_Reset(', [
        ('skip clear', 'ops(collider)->ClearForces();', '(void)collider;'),
        ('wrong identity', 'identity(field(collider, 0x20));', 'identity(field(collider, 0x30));'),
        ('wrong state code', 'state + 0x0c) = 13;', 'state + 0x0c) = 12;'),
    ]),
    ('ph_collider_publish_transform', CORE, 'void phCollider_PublishTransform(', [
        ('wrong flag', 'if (bound[6])', 'if (bound[5])'),
        ('wrong centroid', 'bound + 0x50', 'bound + 0x30'),
        ('correction sign', 'flush(lbl_82606750[i]) - flush(displacement[i])', 'flush(lbl_82606750[i]) + flush(displacement[i])'),
        ('wrong W', 'displacement[3] = displacement[0];', 'displacement[3] = displacement[2];'),
    ]),
    ('ph_articulated_set_linear_velocity_sync', CALLER, 'void rage::phArticulatedCollider::SetVelocityScaled(', [
        ('wrong mass', 'bytes + 0x64', 'bytes + 0x68'),
        ('wrong joint slot', 'this, 0x1d0', 'this, 0x30c'),
    ]),
    ('ph_articulated_set_linear_momentum_sync', CALLER, 'void rage::phArticulatedCollider::SetVelocityAndSync(', [
        ('wrong momentum', '+ 0x100', '+ 0x110'),
        ('wrong propagation', '+ 0xe0', '+ 0x100'),
    ]),
    ('ph_articulated_set_angular_velocity_sync', CALLER, 'void rage::phArticulatedCollider::SyncAfterBaseUpdate(', [
        ('wrong propagation', '+ 0xf0', '+ 0xe0'),
    ]),
    ('ph_articulated_set_angular_momentum_sync', CALLER, 'void rage::phArticulatedCollider::SetAngularVelocity(', [
        ('wrong momentum', '+ 0x110', '+ 0x100'),
    ]),
    ('ph_articulated_reset_collider', CALLER, 'void rage::phArticulatedCollider::Reset(', [
        ('wrong dirty flag', 'bytes[0x1d4]', 'bytes[0x1d5]'),
        ('wrong count', 'bytes + 0x1d8', 'bytes + 0x1dc'),
    ]),
    ('ph_collider_post_integrate', CALLER, 'void rage::phArticulatedCollider::UpdatePostIntegrate(', [
        ('skip publish', 'phCollider_PublishTransform(this);', '(void)this;'),
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
                             Options(trials=60, seed=1, patches=((body, body.replace(old, new)),))).run()
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
