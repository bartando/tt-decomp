"""Mutate build-cache copies only; only behavioral FAIL counts as detection."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'drill_practice_target_set_position': [
        ('ignore lvx alignment', '& ~uintptr_t(15)', '& ~uintptr_t(0)'),
        ('drop w lane', 'alignedPosition, sizeof(target->m_position)', 'alignedPosition, 12'),
        ('boolean clamp low bit', 'target->m_clampToTable != 0', '(target->m_clampToTable & 1) != 0'),
        ('swap table dimensions', 'table->width * 0.5f', 'table->length * 0.5f'),
        ('omit half extent', 'table->length * 0.5f', 'table->length'),
        ('omit lower clamp', 'float raised = delta >= 0.0f ? value : lower;', 'float raised = value;'),
        ('omit upper clamp', 'double(raised) - double(halfExtent) >= 0.0 ? halfExtent : raised', 'raised'),
        ('drop height offset', 'target->m_heightOffset + target->m_position.y', 'target->m_position.y'),
        ('return input pointer', '    return target;\n}', '    return const_cast<float*>(position);\n}'),
    ],
    'drill_hud_remaining': [
        ('wrong key', '"possible", count', '"completed", count'),
        ('wrong value', '"possible", count', '"possible", count + 1'),
        ('omit entry type', '        entry->type = 3;', '        entry->type = 0;'),
        ('drop release', 'if (acquired != 0) hudFlashBase_PublishPageGroup(hud);', 'if (false) hudFlashBase_PublishPageGroup(hud);'),
        ('low bit release test', 'if (acquired != 0) hudFlashBase_PublishPageGroup(hud);', 'if (acquired & 1) hudFlashBase_PublishPageGroup(hud);'),
    ],
    'drill_hud_completed': [
        ('wrong completed key', '"completed", count', '"possible", count'),
        ('wrong completed value', '"completed", count', '"completed", count - 1'),
    ],
    'drill_hud_time_low': [
        ('wrong urgent key', '"time_low", (low & 0xFFu) != 0 ? 1 : 0', '"possible", (low & 0xFFu) != 0 ? 1 : 0'),
        ('omit normalization', '"time_low", (low & 0xFFu) != 0 ? 1 : 0', '"time_low", low'),
        ('urgent low bit only', '"time_low", (low & 0xFFu) != 0 ? 1 : 0', '"time_low", low & 1'),
    ],
    'drill_hud_arrow_direction': [
        ('wrong arrow key', 'group, "arrow_direction"', 'group, "completed"'),
        ('read direction too early', 'void hudTrainingHUD_PushArrowDirection(DrillTrainingHud* hud) {',
         'void hudTrainingHUD_PushArrowDirection(DrillTrainingHud* hud) {\n    int32_t staleDirection = hud->m_arrowDirection;'),
    ],
}


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / 'src/game/drill/pong_drill.cpp').read_text()
    caught = 0
    for spec, cases in CASES.items():
        for name, old, new in cases:
            assert source.count(old) == (2 if old in ('        entry->type = 3;', 'if (acquired != 0) hudFlashBase_PublishPageGroup(hud);') else 1), name
            patches = [(old, new)]
            if name == 'read direction too early':
                patches.append(('int32_t direction = hud->m_arrowDirection;', 'int32_t direction = staleDirection;'))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=256, seed=1, patches=tuple(patches))).run()
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
