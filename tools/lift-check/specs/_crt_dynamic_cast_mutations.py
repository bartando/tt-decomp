"""Prove the RTDynamicCast spec rejects independently broken entry-point behavior."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ('return null for every object', 'if (!object) return nullptr;', 'if (true) return nullptr;'),
    ('ignore complete-object offset', 'input - locator->offset', 'input'),
    ('ignore constructor displacement', 'locator->constructorDisplacementOffset != 0', 'false'),
    ('compare type descriptor identity only', 'if (a == b) return true;', 'return a == b;'),
    ('accept inaccessible base', '(candidate->attributes & 1u) == 0', 'true'),
    ('reverse MI/VI dispatch', '(hierarchy->attributes & 2u) == 0', '(hierarchy->attributes & 2u) != 0'),
    ('ignore vfDelta', 'input - vfDelta - complete', 'input - complete'),
    ('omit virtual-base offset', 'complete + virtualOffset + target->memberDisplacement', 'complete + target->memberDisplacement'),
    ('omit member displacement', 'complete + virtualOffset + target->memberDisplacement', 'complete + virtualOffset'),
    ('suppress bad_cast', 'if (isReference != 0)', 'if (false)'),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/crt/rtti.cpp').read_text()
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, name
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = Checker(Path(__file__).with_name('crt_dynamic_cast.py'),
                             Options(seed=1, patches=((source, source.replace(old, new)),))).run()
        print(f"{'CAUGHT' if result == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if result != 1:
            print(output.getvalue())
            return 1
    print(f'Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
