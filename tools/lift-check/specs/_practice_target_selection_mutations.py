"""Only behavioral FAIL counts; source patches are confined to build-cache copies."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'match_practice_target_shuffle': [
        ('lose carry', '0x5CDCFAA7u + g_prngState[1]', '0x5CDCFAA7u'),
        ('allow self swap', 'j = i + 1 + bits % (array->m_count - i - 1);', 'j = i + bits % (array->m_count - i);'),
        ('use 23 random bits', 'AdvancePracticeTargetRandom() & 0x7FFFFFFFu', 'AdvancePracticeTargetRandom() & 0x7FFFFFu'),
        ('skip final swap', 'i < array->m_count - 1;', 'i < array->m_count - 2;'),
        ('lose swapped word', 'array->m_data[j] = saved;', 'array->m_data[j] = 0;'),
        ('retain cursor', '    array->field_0C = 0;', '    /* cursor reset lost */'),
    ],
    'match_practice_target_next': [
        ('select next word', 'array->m_data[array->field_0C];', 'array->m_data[(array->field_0C + 1) % array->m_count];'),
        ('never wrap cursor', '(array->field_0C + 1) % array->m_count', 'array->field_0C + 1'),
        ('ignore shuffle flag', 'array->field_0C == 0 && (array->m_flags & 0x80)', 'false'),
        ('swap flag bits', '(array->m_flags & 0x40) ? 1u : 0u', '(array->m_flags & 0x80) ? 1u : 0u'),
    ],
    'match_practice_target_layout_grid': [
        ('wrong width scale', 'table->width * 0.5f', 'table->width'),
        ('wrong length scale', 'table->length * 0.5f', 'table->width * 0.5f'),
        ('swap boundary axes', 'g_practiceTargetGridShape[4 + i]', 'g_practiceTargetGridShape[i]'),
        ('skip last grid row', 'row < 3;', 'row < 2;'),
        ('wrong upper x', 'zone[6] = x[col + 1];', 'zone[6] = x[col];'),
        ('wrong upper z', 'zone[7] = z[row + 1];', 'zone[7] = z[row];'),
    ],
    'match_practice_target_select_set': [
        ('force set reload', 'if (setId != static_cast<int32_t>(target->field_44))', 'if (true)'),
        ('omit selected set', 'target->field_44 = setId;', '/* selected set lost */'),
        ('lose capacity fallback', 'count == -1 ? array->m_capacity : count', 'count'),
        ('retain previous order', 'array->m_data[i] = i;', '(void)i;'),
        ('omit selected index', 'g_practiceTargetSelectedIndex = index;', '/* selected index lost */'),
        ('wrong active zone source', 'selected.activeZones[i]', 'selected.activeZones[8 - i]'),
        ('wrong shape half', 'selected.gridShape[i]', 'selected.gridShape[(i + 4) % 8]'),
        ('omit grid rebuild', '    gmPracticeTarget_LayOutTableGrid();\n}', '    /* grid update lost */\n}'),
    ],
}


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/game/match/pong_match.cpp').read_text()
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
