"""Only behavioral FAIL counts; patch cache copies, not source files."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('omit completion callback', '        sysCallback_Invoke(&completion, 0);', '        ;'),
    ('wrong callback slot', 'sysCallback_Invoke(&completion, 0);', 'sysCallback_Invoke(&callbacks[0], 0);'),
    ('ignore high mode bits', 'if (completion.mode != 0)', 'if ((completion.mode & 1) != 0)'),
    ('omit begin reset', '    callbacks[0] = completion;', '    ;'),
    ('wrong reset context', 'completion.context = g_sceneResetMatrix[2];', 'completion.context = g_sceneResetMatrix[1];'),
    ('wrong reset mode', 'completion.mode = g_sceneResetMatrix[3];', 'completion.mode = 0;'),
]


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/game/pong_render.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == 1, name
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = Checker(Path(__file__).with_name('screen_transition_end.py'),
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
