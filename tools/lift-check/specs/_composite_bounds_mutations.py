"""Behavioral mutation proof for composite AABB/radius and refresh dispatch."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CORE = 'src/physics/composite_bounds.cpp'
CASES = [
    ('ph_composite_compute_radius', CORE, 'float refinedLength(', [
        ('ignore reciprocal sentinel', 'estimate == flushCompositeVmx(lbl_82619BF0[0]) ? lbl_82606750[0] : estimate', 'estimate'),
        ('skip Newton refinement', 'return multiplyCompositeVmx(squared, refined);', 'return multiplyCompositeVmx(squared, inverse);'),
    ]),
    ('ph_composite_compute_radius', CORE, 'float phBoundComposite_ComputeRadius(', [
        ('wrong child stride', 'children[index].get()', 'children[0].get()'),
        ('wrong matrix stride', 'index * 16', 'index * 12'),
        ('skip homogeneous translation', 'lbl_82619BD0[lane]', '0'),
        ('skip centroid mask', 'lbl_82619BE0[lane]', '0xffffffffu'),
        ('transpose basis', 'matrix[axis], matrix[4 + axis], matrix[8 + axis], matrix[12 + axis]', 'matrix[axis * 4], matrix[axis * 4 + 1], matrix[axis * 4 + 2], matrix[axis * 4 + 3]'),
        ('omit query center', 'subtractCompositeVmx(dotCompositeVmx(homogeneous, column, 4), center[axis])', 'dotCompositeVmx(homogeneous, column, 4)'),
        ('omit part radius', 'child[2] + refinedLength(delta)', 'refinedLength(delta)'),
        ('keep minimum', 'difference >= 0.0f ? radius : candidate', 'difference >= 0.0f ? candidate : radius'),
    ]),
    ('ph_composite_rebuild_extents', CORE, 'float transformedCorner(', [
        ('wrong upper corner selection', 'upper ? (difference >= 0.0f ? b : a)', 'upper ? (difference >= 0.0f ? a : b)'),
        ('wrong scalar sum order', '((terms[2] + terms[1]) + terms[0]) + matrix[12]', '((matrix[12] + terms[2]) + terms[1]) + terms[0]'),
    ]),
    ('ph_composite_rebuild_extents', CORE, 'void phBoundComposite_RebuildExtents(', [
        ('wrong minimum union', 'difference >= 0.0f ? corner : old', 'difference >= 0.0f ? old : corner'),
        ('wrong maximum union', 'difference >= 0.0f ? old : corner', 'difference >= 0.0f ? corner : old'),
        ('skip empty lower reset', 'std::memset(bytes + 0x20, 0, 16);', '(void)bytes;'),
        ('leave empty W lane', 'std::memset(bytes + 0x10, 0, 16);', 'std::memset(bytes + 0x10, 0, 12);'),
        ('forget center half', 'lbl_825CB7D0[lane]', '1.0f'),
        ('omit displacement flag', 'bytes[5] = displaced;', 'bytes[5] = 0;'),
        ('store squared origin radius', 'values[3] = float(crt_sqrt(squared));', 'values[3] = squared;'),
    ]),
    ('ph_composite_refresh_bounds', 'src/game/creature/pong_creature.cpp', 'extern "C" void pongCreatureInst_E828_v12(', [
        ('skip AABB rebuild', 'rage::phBoundComposite_RebuildExtents(self);', '(void)self;'),
        ('wrong output radius field', 'values[2] =', 'values[3] ='),
        ('test full symmetry flags', 'static_cast<uint8_t>(flags) != 0', 'flags != 0'),
    ]),
    ('ph_composite_symmetrize_bounds', CORE, 'void phBoundComposite_Symmetrize(', [
        ('wrong magnitude side', '__builtin_fabsf(upper) < __builtin_fabsf(lower)', '__builtin_fabsf(upper) > __builtin_fabsf(lower)'),
        ('wrong magnitude tie', '__builtin_fabsf(upper) < __builtin_fabsf(lower)', '__builtin_fabsf(upper) <= __builtin_fabsf(lower)'),
        ('leave Z asymmetric', 'axis < 3', 'axis < 2'),
        ('omit half diagonal', 'refinedLength(width) * 0.5f', 'refinedLength(width)'),
        ('leave origin radius', 'values[3] = radius;', '(void)radius;'),
        ('leave centroid W', '+ 0x30, 0, 16', '+ 0x30, 0, 12'),
    ]),

]


def main():
    total = 0
    for spec, path, signature, mutations in CASES:
        source = (ROOT / path).read_text()
        start = source.index(signature)
        body = source[start:source.index('\n}', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) >= 1, (spec, name, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                    Options(trials=160, seed=1, patches=((body, body.replace(old, new, 1)),))).run()
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
