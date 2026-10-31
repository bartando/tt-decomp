"""Require behavioral failures for deliberate weight-ABI regressions; patch cache only."""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("truncate forwarded ID", "animPair[0], animID, &index", "animPair[0], uint16_t(animID), &index"),
    ("reject high type bits", "const uint8_t channel = static_cast<uint8_t>(type)", "const uint32_t channel = type"),
    ("inline weights instead of pointer", "*(float**)((char*)animPair[1] + 16)",
     "(float*)((char*)animPair[1] + 16)"),
    ("wrong weight stride", "(uint32_t)index << 2", "(uint32_t)index << 1"),
    ("accept zero weight", "return weight > g_floatZero;", "return weight >= g_floatZero;"),
    ("accept NaN weight", "return weight > g_floatZero;", "return !(weight <= g_floatZero);"),
    ("reject rotation channels", "if (channel != 0 && channel != 1)", "if (channel != 0)"),
    ("omit weight output", "*outWeight = weight;", "(void)outWeight;"),
    ("always read first weight", "(uint32_t)index << 2", "0"),

]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/game/creature/pong_creature.cpp').read_text()
    count = 0
    for signature, mutations in [('uint32_t LocomotionStateAnim_81A8(', MUTATIONS)]:
        start = source.index('\n' + signature) + 1
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, label
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name('locomotion_state_anim_81a8.py'),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f'MISSED {label}: BUILD {exc}', flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and 'faulted' not in report
            print(f"{'CAUGHT' if caught else 'MISSED'} {label}: " +
             (report.splitlines()[0] if report else 'no checker output'), flush=True)
            if not caught:
                print(report)
                return 1
            count += 1
    print(f'Caught {count}/{count} mutations', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
