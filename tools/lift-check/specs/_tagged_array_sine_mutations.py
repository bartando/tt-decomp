"""Mutation proof for tagged array allocation and SWF sine ABI."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = [
    ('ph_allocate_tagged_array', 'src/physics/ph_physics.cpp', 'void* phBoundCapsule_AllocArray(', [
        ('wrong product', 'static_cast<uint32_t>(elemSize) * static_cast<uint32_t>(count)', 'static_cast<uint32_t>(elemSize) + static_cast<uint32_t>(count)'),
        ('wrong attributes', '0x648a0018u', '0x64890018u'),
        ('drop allocated pointer', 'return rage_AllocInternal(totalSize, 0x648a0018u);', 'rage_AllocInternal(totalSize, 0x648a0018u); return nullptr;'),
    ]),
    ('swf_math_sin', 'src/physics/ph_physics.cpp', 'extern "C" void swfMathSin(', [
        ('wrong tag', 'output->tag = 4;', 'output->tag = 0;'),
        ('late tag store', 'output->tag = 4;\n    const float angle = swfValueToFloat(input);', 'const float angle = swfValueToFloat(input);\n    output->tag = 4;'),
        ('wrong sine sign', 'static_cast<float>(crt_sin(angle))', '-static_cast<float>(crt_sin(angle))'),
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
