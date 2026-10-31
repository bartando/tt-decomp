"""Behavioral mutations for the visual spin and shared basis rebuild lifts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('rage_mat33_orthonormalize', 'src/rage/math/mat33_orthonormalize.cpp', [
        ('empty rebuild', '    alignas(16) float first[4],second[4],third[4];', '    return;\n    alignas(16) float first[4],second[4],third[4];'),
        ('reverse handedness', 'CrossBasis(first,second,third);', 'CrossBasis(first,third,second);'),
        ('wrong second cross', 'CrossBasis(second,third,first);', 'CrossBasis(second,first,third);'),
        ('skip first normalization', 'NormalizeBasis(first);', '(void)first;'),
        ('skip third normalization', 'NormalizeBasis(third);', '(void)third;'),
        ('overwrite translation', '__builtin_memcpy(matrix+8,third,16);', '__builtin_memcpy(matrix+12,third,16);'),
        ('skip W lane', 'lane<4;', 'lane<3;'),
        ('wrong normalization correction', 'error*half', 'error*inverse'),
    ]),
    ('ball_integrate_visual_spin', 'src/game/ball/ball_visual_spin.cpp', [
        ('empty integration', '    const float scale=', '    return;\n    const float scale='),
        ('ignore frame duration', 'node->visualSpinScale*dt', 'node->visualSpinScale'),
        ('ignore node scale', 'node->visualSpinScale*dt', 'dt'),
        ('lose Z spin', 'z=increment[2]', 'z=increment[1]'),
        ('skip small increments', 'square>0x1p-126f', 'square>1.0f'),
        ('wrong rotation angle', 'rotation,axis,angle)', 'rotation,axis,square)'),
        ('omit composition', 'rage::mat33ComposeInPlace(matrix,rotation);', '(void)rotation;'),
        ('omit basis repair', 'rage::mat33Orthonormalize(matrix);', '(void)matrix;'),
    ]),
]

def main():
    root=Path(__file__).resolve().parents[3]
    total=0
    for spec,path,mutations in CASES:
        source=(root/path).read_text()
        for label,old,new in mutations:
            assert old in source,(spec,label)
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=96,seed=1,patches=((source,source.replace(old,new)),))).run()
            print(f"{'CAUGHT' if rc==1 else 'MISSED'} {spec}: {label}: {output.getvalue().splitlines()[0]}",flush=True)
            if rc!=1:
                print(output.getvalue())
                return 1
            total+=1
    print(f'Caught {total}/{total} mutations',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
