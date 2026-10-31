"""Mutation proof for both physics reference domains and bound replacement."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/physics/archetype_refs.cpp'
CASES = [
    ('ph_archetype_release', 'extern "C" uint32_t util_9D98(', [
        ('wrong disabled result', 'if (!g_phInstrumentEnabled) return 1;', 'if (!g_phInstrumentEnabled) return 0;'),
        ('wrong refcount field', 'bytes + 0x1a', 'bytes + 0x60'),
        ('increment instead of decrement', '*count - 1', '*count + 1'),
        ('lose remaining count', 'if (*count != 0) return *count;', 'if (*count != 0) return 1;'),
        ('test full delete flag', '(deleteWhenUnused & 0xff) != 0', 'deleteWhenUnused != 0'),
        ('wrong scalar flags', 'ops->Destroy(1);', 'ops->Destroy(2);'),
        ('skip retained reset', 'ops->OnZeroReferences();', '(void)ops;'),
    ]),
    ('ph_bound_release', 'uint32_t ph_CEE0(', [
        ('wrong disabled result', 'if (!g_phInstrumentEnabled) return 1;', 'if (!g_phInstrumentEnabled) return 0;'),
        ('wrong refcount field', 'bytes + 0x60', 'bytes + 0x1a'),
        ('skip decrement', '*count = static_cast<uint16_t>(*count - 1);', '*count = *count;'),
        ('test full delete flag', '(deleteWhenUnused & 0xff) != 0', 'deleteWhenUnused != 0'),
        ('skip scalar delete', 'static_cast<PhysicsReferenceOps*>(bound)->Destroy(1);', '(void)bound;'),
    ]),
    ('ph_archetype_set_bound', 'void ph_9E50(', [
        ('skip retain', '*count = static_cast<uint16_t>(*count + 1);', '*count = *count;'),
        ('wrong bound refcount', '+ 0x60)', '+ 0x1a)'),
        ('skip old release', 'ph_CEE0(existing, 1);', '(void)existing;'),
        ('wrong release flags', 'ph_CEE0(existing, 1);', 'ph_CEE0(existing, 0);'),
        ('clear new bound', '= newBound;', '= nullptr;'),
    ]),
]


def main():
    total = 0
    for spec, signature, mutations in CASES:
        source = (ROOT / SOURCE).read_text()
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
