"""Mutation regression for the second pointer-based SetPosition caller."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = (
    ('wrong first random mask', 'AdvancePracticeTargetRandom() & 0x7FFFFFu', 'AdvancePracticeTargetRandom() & 0x3FFFFFu'),
    ('reverse x range', 'float xRange = xUpper - xLower;', 'float xRange = xLower - xUpper;'),
    ('drop near-edge margin', '(margin - halfLength) - g_practiceTargetNearEdge', 'margin - halfLength'),
    ('wrong y origin', '        table->height,', '        0.0f,'),
    ('wrong radius lane', '        margin\n    };', '        1.0f\n    };'),
    ('reverse z origin', '__builtin_fmaf(randomZ, zRange, -margin)', '__builtin_fmaf(randomZ, zRange, margin)'),
    ('omit setter call', '    gmPracticeTarget_SetPosition(target, position);', '    /* setter lost */'),
)


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/game/match/pong_match.cpp').read_text()
    for name, old, new in CASES:
        assert source.count(old) == (2 if name == 'wrong first random mask' else 1), name
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name('match_practice_target_place_randomly.py'),
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
