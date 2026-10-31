"""Require behavioral FAILs for animation pair/processing regressions."""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ('locomotion_fetch_animation_pair','bool LocomotionStateAnim_C358_g(', [
        ('empty pair','    auto* list','    return false;\n    auto* list'),
        ('skip second lookup','list->FindAnimationByID(secondType, 0)','list->FindAnimationByID(firstType, 0)'),
        ('wrong vector getter','first->GetTranslation()','first->GetQuaternion()'),
        ('wrong quaternion getter','second->GetQuaternion()','second->GetTranslation()'),
        ('wrong translation row','reinterpret_cast<uintptr_t>(out) + 16','reinterpret_cast<uintptr_t>(out)'),
        ('omit quaternion w','lane < 4','lane < 3'),
        ('omit translation w','reinterpret_cast<void*>(position), vector, 16','reinterpret_cast<void*>(position), vector, 12'),
        ('wrong success return','return true;','return false;'),
    ]),
    ('locomotion_process_animation_list','void LocomotionStateAnim::ProcessAnimationList(', [
        ('empty processing','    if (!animationList)','    return;\n    if (!animationList)'),
        ('wrong evaluation flags','animationField<void*>(container, 4), 0, 1','animationField<void*>(container, 4), 1, 0'),
        ('wrong dispatch flag','data, 0x14) & 1','data, 0x14) & 2'),
        ('wrong channel weight','const float weight = g_floatZero','const float weight = 1.0f'),
        ('skip channels','const uint32_t count = animationField<uint16_t>(frame, 0x0C)','const uint32_t count = 0'),
        ('cache array across callbacks','for (uint32_t i = 0; i < count; ++i) {\n            void** entries = animationField<void**>(frame, 8);',
         'void** entries = animationField<void**>(frame, 8);\n        for (uint32_t i = 0; i < count; ++i) {'),
        ('omit skeleton rebuild','LocomotionStateAnim_C8F8_g(animationList);','(void)animationList;'),
    ]),
    ('locomotion_setup_anim_node','void LocomotionStateAnim_10D8(', [
        ('empty node','    if (!container)','    return;\n    if (!container)'),
        ('always use default clip','if (!container)','if (true)'),
        ('fallback for zero phase','time < g_floatZero','time <= g_floatZero'),
        ('fallback for NaN phase','time < g_floatZero','!(time >= g_floatZero)'),
        ('wrong evaluator flags','animationField<void*>(self, 0x1C), 0, 1, time','animationField<void*>(self, 0x1C), 1, 0, time'),
        ('wrong pair channels','0, 1, 0, pair','1, 0, 0, pair'),
        ('omit quaternion conversion','LocomotionStateAnim_AD30_g(static_cast<float*>(dst), pair);','(void)dst;'),
        ('copy quaternion as translation','pair + 4, 16','pair, 16'),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/game/creature/pong_creature.cpp').read_text()
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
