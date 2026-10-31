"""Mutation proof for locked interface retention and pointer publication."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = [
    ('ph_object_add_ref_locked', 'src/physics/locked_interface.cpp', 'uint32_t phObject_AddRefLocked(', [
        ('skip lock', 'RtlEnterCriticalSection(lock);', '(void)lock;'),
        ('skip unlock', 'RtlLeaveCriticalSection(lock);', '(void)lock;'),
        ('drop result', 'return result;', 'return 0;'),
    ]),
    ('movie_query_retained_interface', 'src/game/misc/pong_misc.cpp', 'int CCalMoviePlayer::QueryPhysicsInstance(', [
        ('stale interface pointer',
         'phObject_AddRefLocked(rage::load_ptr32<void>(this, 0x38));\n    *static_cast<rage::ptr32<void>*>(outResult) = rage::load_ptr32<void>(this, 0x38);',
         'void* original = rage::load_ptr32<void>(this, 0x38);\n    phObject_AddRefLocked(original);\n    *static_cast<rage::ptr32<void>*>(outResult) = original;'),
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
