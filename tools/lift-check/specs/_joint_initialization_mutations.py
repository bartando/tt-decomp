"""Behavioral mutation proof for vector construction and joint block reset."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = [
    ('lf_vector_ctor_iterator', 'src/physics/ph_update_object.cpp', 'void phJoint3Dof_0170_g(', [
        ('skip final ctor', 'remaining >= 0', 'remaining > 0'),
        ('wrong stride', 'current += stride;', 'current += 16;'),
    ]),
    ('ph_joint_block_reset', 'src/physics/ph_update_object.cpp', 'void util_4628(', [
        ('skip final record', 'i < count', 'i < count - 1'),
        ('wrong sentinel', 'record[1] = lbl_825C5938;', 'record[1] = lbl_8202D110;'),
        ('wrong record stride', 'block + i * 64', 'block + i * 48'),
        ('wrong flag', 'flags[57] = 1;', 'flags[57] = 0;'),
        ('wrong default', 'defaults[3] = g_phClampMax;', 'defaults[3] = g_phCapsuleShapeK;'),
    ]),
    ('ph_joint_chain_constructor', 'src/physics/ph_physics.cpp', 'void* phJointChain_Constructor(', [
        ('skip block', 'i = 15', 'i = 14'),
        ('wrong element count', 'jointSlot, 144, 20', 'jointSlot, 144, 19'),
        ('wrong element stride', 'jointSlot, 144, 20', 'jointSlot, 140, 20'),
        ('wrong block stride', 'jointSlot += 3016;', 'jointSlot += 3000;'),
        ('leave enabled', '*(uint8_t*)(obj + 4) = 0;', '(void)obj;'),
    ]),
    ('ph_joint_four_block_constructor', 'src/physics/ph_physics.cpp', 'phJoint3Dof* phJoint3Dof_C4F8_w(', [
        ('skip block', 'block < 4', 'block < 3'),
        ('wrong reset count', 'current + 0x210) = 3', 'current + 0x210) = 2'),
        ('wrong secondary count', 'current + 0x212) = 3', 'current + 0x212) = 2'),
        ('skip reset', 'util_4628(current);', '(void)current;'),
    ]),
]

def main():
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (ROOT / source_path).read_text()
        start = source.index(signature)
        body = source[start:source.index('\n}\n', start) + 2]
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
