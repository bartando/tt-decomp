"""Run from the repo root with PYTHONPATH=tools/lift-check and its venv Python."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

SHARED = [
    ("wrong bank", '(handle & 1) != 0', '(handle & 1) == 0'),
    ("wrong dirty byte", 'dirty[bit >> 3] |=', 'dirty[bit >> 4] |='),
    ("wrong dirty mask", 'dirty[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7]', 'dirty[bit >> 3] |= g_shaderParameterDirtyMasks[(bit + 1) & 7]'),
    ("wrong descriptor index", '(handle >> 18) * 8', '(handle >> 19) * 8'),
    ("wrong value slot", 'return values + slot * 16;', 'return values + ((slot + 1) & 0xff) * 16;'),
]
SPECIFIC = {
    'float': [("increment counter", '--*counter;\n    uint8_t* target', '++*counter;\n    uint8_t* target'),
              ("drop scalar write", 'std::memcpy(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(target) & ~uintptr_t(3)), &value, sizeof(value));', '(void)target;')],
    'vector': [("increment counter", '--*counter;\n    // lvx', '++*counter;\n    // lvx'),
               ("drop vector write", 'std::memcpy(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(target) & ~uintptr_t(15)), vector, 16);', '(void)target;'),
               ("truncate vector", 'vector, 16);\n}', 'vector, 8);\n}')],
}

def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/rage/rage_grm.cpp').read_text()
    for kind in ('float', 'vector'):
        spec = Path(__file__).with_name(f'grm_shader_parameter_set_{kind}.py')
        mutations = SHARED + SPECIFIC[kind]
        for name, old, new in mutations:
            assert source.count(old) == 1, f'mutation anchor changed: {name}'
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
            print(f'{kind}: {"CAUGHT" if rc == 1 else "MISSED"} {name}: {output.getvalue().splitlines()[0]}', flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        print(f'{kind}: caught {len(mutations)}/{len(mutations)} mutations', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
