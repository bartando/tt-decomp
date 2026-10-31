"""Only behavioral FAILs count; mutate cached build copies, never source files.
Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python this_file.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'drill_base_next_attempt': [
        ('drop drill-type exemption', 'GetDrillTypeIndex() != 5 && m_numAttempts > 0',
         'GetDrillTypeIndex() != 6 && m_numAttempts > 0'),
        ('count first attempt as miss', '&& m_numAttempts > 0 &&', '&& m_numAttempts >= 0 &&'),
        ('ignore completed success', 'm_prevSuccesses == m_numSuccesses && !m_completionFlag',
         'true && !m_completionFlag'),
        ('ignore miss suppression', '&& !m_completionFlag)', '&& true)'),
        ('omit success snapshot', 'm_prevSuccesses = m_numSuccesses;', 'm_prevSuccesses = 0;'),
        ('drop attempt increment', 'static_cast<uint32_t>(m_numAttempts) + count',
         'static_cast<uint32_t>(m_numAttempts)'),
        ('retain miss flag', '    m_completionFlag = 0;\n    g_pBallRobot',
         '    m_completionFlag = 1;\n    g_pBallRobot'),
        ('omit robot mode', 'g_pBallRobot->m_mode = GetRobotMode();', '(void)GetRobotMode();'),
        ('omit target refresh', '    ApplyTargetSet();\n    hudTrainingHUD_SetRemaining',
         '    /* target refresh lost */\n    hudTrainingHUD_SetRemaining'),
        ('remaining off by one', 'm_pConfig->m_totalNumTries - m_numAttempts + 1',
         'm_pConfig->m_totalNumTries - m_numAttempts'),
        ('boolean low bit only', 'if (UseAlternateAttemptEvent())', 'if (UseAlternateAttemptEvent() & 1)'),
        ('wrong ordinary event', 'NotifyUIEvent(0x0F, 0x40, 0, 0);', 'NotifyUIEvent(0x0E, 0x40, 0, 0);'),
        ('drop final message', '    NotifyUIEvent(0x5005, 0x40, 0, 0);', '    /* event lost */'),
    ],
    'drill_base_choose_robot_target': [
        ('easy boundary', 'm_numAttempts <= m_pConfig->m_numEasyShots',
         'm_numAttempts < m_pConfig->m_numEasyShots'),
        ('skip centered target', 'if (x == 0.0f)', 'if (x == 1.0f)'),
        ('lose selected target', 'm_targetIndex = i;', 'm_targetIndex = 0;'),
        ('ignore repeat probability', 'NextRandomBits() * g_fPrngNormalize < m_pConfig->m_probSameShot',
         'NextRandomBits() * g_fPrngNormalize < 0.0f'),
        ('allow previous target', 'if (i != previous) choices[count++] = i;',
         'if (true) choices[count++] = i;'),
        ('use 23-bit choice draw', 'g_prngState[0] & 0x7FFFFFFFu', 'g_prngState[0] & 0x7FFFFFu'),
        ('lose target z', '*output = targets[m_targetIndex];\n}',
         'output->x = targets[m_targetIndex].x;\n}'),
    ],
    'drill_round_half_away_from_zero': [
        ('wrong positive half', 'value + 0.5f : value - 0.5f', 'value + 0.4f : value - 0.5f'),
        ('wrong negative sign', 'value + 0.5f : value - 0.5f', 'value + 0.5f : value + 0.5f'),
        ('wrong positive saturation', 'return INT32_MAX;', 'return INT32_MIN;'),
        ('wrong NaN conversion', 'if (rounded != rounded || rounded < -2147483648.0f) return INT32_MIN;',
         'if (rounded != rounded) return 0; if (rounded < -2147483648.0f) return INT32_MIN;'),
    ],
}


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/game/drill/pong_drill.cpp').read_text()
    caught = 0
    for spec, cases in CASES.items():
        for name, old, new in cases:
            assert source.count(old) == 1, (name, source.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=256, seed=1, patches=((old, new),))).run()
            first = output.getvalue().splitlines()[0]
            detected = rc == 1 and first.startswith('FAIL ')
            print(f"{'CAUGHT' if detected else 'MISSED'} {spec}: {name}: {first}", flush=True)
            if not detected:
                print(output.getvalue())
                return 1
            caught += 1
    print(f'Caught {caught}/{sum(map(len, CASES.values()))} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
