"""Require behavioral FAILs for channel applier/rebuild regressions."""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ('blend_locomotion_anims','src/anim/locomotion.cpp','void LocomotionStateAnim_C128_g(', [
        ('empty lift','    (void)unusedR4;','    return;\n    (void)unusedR4;'),
        ('skip rotations','if (type == 1)','if (false)'),
        ('wrong quaternion getter','->GetQuaternion()','->GetTranslation()'),
        ('wrong bone stride','index * 0x50','index * 0x40'),
        ('omit translation w','record + 0x30, vector, sizeof(vector)','record + 0x30, vector, 12'),
        ('wrong translation offset','record + 0x30, vector','record + 0x20, vector'),
        ('lose VMX alignment','reinterpret_cast<uintptr_t>(translation) & ~uintptr_t(15)','reinterpret_cast<uintptr_t>(translation)'),
    ]),
    ('transition_locomotion_state','src/anim/locomotion.cpp','void LocomotionStateAnim_C288_g(', [
        ('empty lift','    (void)unusedR4;','    return;\n    (void)unusedR4;'),
        ('skip rotations','if (type == 1)','if (false)'),
        ('wrong quaternion getter','->GetQuaternion()','->GetTranslation()'),
        ('wrong bone stride','index * 0x50','index * 0x40'),
        ('omit translation w','records + 0x30, vector, sizeof(vector)','records + 0x30, vector, 12'),
        ('wrong translation offset','records + 0x30, vector','records + 0x20, vector'),
        ('wrong root ID','channel + 6) == 0','channel + 6) == 1'),
        ('lose VMX alignment','reinterpret_cast<uintptr_t>(translation) & ~uintptr_t(15)','reinterpret_cast<uintptr_t>(translation)'),
    ]),
    ('creature_copy_animation_data','src/game/creature/pong_creature.cpp','void LocomotionStateAnim_C8F8_g(', [
        ('empty rebuild','    const skeletonPoseView* skel','    return;\n    const skeletonPoseView* skel'),
        ('omit root composition','if (skel->rootHelper != nullptr)','if (false)'),
        ('omit root row','row < 4','row < 3'),
        ('skip last bone','i < boneCount','i + 1 < boneCount'),
        ('wrong output stride','skel->matrices + 0x40 * i','skel->matrices + 0x20 * i'),
        ('wrong parent index','parents[i]','parents[0]'),
        ('reload snapshotted table','parents[i]','data->parents[i]'),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    count = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
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
