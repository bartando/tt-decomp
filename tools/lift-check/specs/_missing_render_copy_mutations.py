"""Only behavioral FAILs count; source edits stay in the build cache."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = (
    ('omit light records', '    pongLightState_CopyLights(dst, src);', '    /* copy lost */'),
    ('omit ambient', '    dst->ambient = src->ambient;', '    /* ambient lost */'),
    ('omit light count', '    dst->count = src->count;', '    /* count lost */'),
    ('omit trailing halfword', '    dst->field_212 = src->field_212;', '    /* field lost */'),
    ('overwrite padding', '    dst->field_212 = src->field_212;', '    dst->field_212 = src->field_212;\n    reinterpret_cast<uint32_t*>(dst)[0x214 / 4] = 0;'),
    ('return source', '    dst->field_212 = src->field_212;\n    return dst;',
     '    dst->field_212 = src->field_212;\n    return const_cast<pongLightState*>(src);'),
)


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/game/pong_render.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, name
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name('render_light_state_copy.py'),
                         Options(trials=256, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith('FAIL ')
        print(f"{'CAUGHT' if caught else 'MISSED'} {name}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f'Caught {len(CASES)}/{len(CASES)} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
