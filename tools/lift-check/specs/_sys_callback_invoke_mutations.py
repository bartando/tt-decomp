"""Only behavioral FAIL counts; patch compiled cache copies, never the source."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('drop bound argument', '>(target)(self, argument);', '>(target)(self, callback->context);'),
    ('drop unbound argument', '>(target)(argument);', '>(target)(callback->context);'),
    ('wrong bound context', '>(target)(self, callback->context);', '>(target)(self, argument);'),
    ('wrong unbound context', '>(target)(callback->context);', '>(target)(argument);'),
    ('swap bound arguments', '>(target)(self, callback->context, argument);', '>(target)(self, argument, callback->context);'),
    ('swap unbound arguments', '>(target)(callback->context, argument);', '>(target)(argument, callback->context);'),
    ('skip unbound calls', 'if (self != nullptr) {', 'if (true) {'),
    ('ignore mode', 'if (mode == 0) return;', 'if (mode != 1) return;'),
]


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/core/rage_core_utils.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, name
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(Path(__file__).with_name('sys_callback_invoke.py'),
                         Options(trials=256, seed=1, patches=((old, new),))).run()
        first = out.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith('FAIL ')
        print(f"{'CAUGHT' if caught else 'MISSED'} {name}: {first}", flush=True)
        if not caught:
            print(out.getvalue())
            return 1
    print(f'Caught {len(CASES)}/{len(CASES)} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
