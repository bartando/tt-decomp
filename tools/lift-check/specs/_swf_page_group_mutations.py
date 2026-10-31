"""Only behavioral FAIL counts. Mutations affect build-cache copies only."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
 'swf_select_page_group': [
  ('ignore active group', 'if (group->active != 0) return;', 'if (false) return;'),
  ('active low bit only', 'if (group->active != 0) return;', 'if ((group->active & 1) != 0) return;'),
  ('wrong node pool', 'g_swfNodePool = group->nodePool;', 'g_swfNodePool = group->memberPool;'),
  ('wrong array pool', 'g_swfScriptArrayPool = group->arrayPool;', 'g_swfScriptArrayPool = group->objectPool;'),
  ('ignore selector low byte', '(bindGlobals & 0xFFu) != 0', 'bindGlobals != 0'),
  ('selector low bit only', '(bindGlobals & 0xFFu) != 0', '(bindGlobals & 1) != 0'),
  ('omit scope binding', 'rage::g_swfGlobalScope = group->globalScope;', '/* scope binding lost */'),
 ],
 'swf_bind_entry': [
  ('wrong binding selector', 'swfSelectPageGroup(group, 1);', 'swfSelectPageGroup(group, 0);'),
  ('omit missing entry insertion', 'swfSetMember(scope->members, key, zeroNumber);', '/* insertion lost */'),
  ('wrong default value', 'zeroNumber[2] = {0, 3}', 'zeroNumber[2] = {1, 3}'),
  ('wrong default type', 'zeroNumber[2] = {0, 3}', 'zeroNumber[2] = {0, 4}'),
  ('reload scope on retry', 'entry = swfFindMember(scope->members, key);\n    }',
   'entry = swfFindMember(static_cast<SwfScopeView*>(rage::g_swfGlobalScope)->members, key);\n    }'),
  ('omit scope cleanup', 'rage::g_swfGlobalScope = nullptr;', '/* scope clear lost */'),
  ('clear active context', 'if (group->active == 0)', 'if (true)'),
  ('omit auxiliary cleanup', 'rage::g_swfAuxiliaryScope = nullptr;', '/* auxiliary clear lost */'),
  ('clear retained array pool', 'g_swfTextPool = nullptr;', 'g_swfTextPool = nullptr;\n        g_swfScriptArrayPool = nullptr;'),
 ],
}


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/swf_page_group.cpp').read_text()
    caught = 0
    for spec, cases in CASES.items():
        for name, old, new in cases:
            assert source.count(old) == 1, name
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
