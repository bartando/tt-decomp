"""Mutation proof for retained vtables, vector/byte copy ranges and refcounts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = [
    ('ph_bound_copy_properties', 'src/physics/bound_copy.cpp', 'void phBound_CopyProperties(', [
        ('overwrite vtable', 'unsigned offset = 4;', 'unsigned offset = 0;'),
        ('omit final base vector', 'offset < 0x60', 'offset < 0x50'),
        ('copy only vector xyz', 'std::memcpy(out + offset, row, 16);', 'std::memcpy(out + offset, row, 12);'),
        ('skip reference count', '*reinterpret_cast<uint16_t*>(out + 0x60) = *reinterpret_cast<const uint16_t*>(in + 0x60);', '(void)out;'),
        ('skip last parameter byte', 'offset < 0x70', 'offset < 0x6f'),
    ]),
    ('ph_capsule_copy_properties', 'src/physics/ph_physics.cpp', 'void rage::phBoundCapsule::CopyFrom(', [
        ('skip base payload', 'rage::phBound_CopyProperties(this, source);', '(void)source;'),
        ('omit last capsule vector', 'offset < 0xc0', 'offset < 0xb0'),
        ('skip material word', '*reinterpret_cast<uint32_t*>(out + 0xc0) = *reinterpret_cast<const uint32_t*>(in + 0xc0);', '(void)out;'),
        ('omit last capsule parameter', 'offset < 0xd0', 'offset < 0xcf'),
        ('wrong reference count', '*reinterpret_cast<uint16_t*>(out + 0x60) = 1;', '*reinterpret_cast<uint16_t*>(out + 0x60) = 0;'),
    ]),
    ('ph_bound_copy_from', 'src/physics/ph_physics.cpp', 'void phBound::CopyFrom(', [
        ('skip base payload', 'rage::phBound_CopyProperties(this, src);', '(void)src;'),
        ('wrong reference count', '= 1u;  // m_nRefCount = 1', '= 0u;  // m_nRefCount = 1'),
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
