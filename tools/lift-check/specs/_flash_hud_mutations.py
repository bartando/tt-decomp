"""Only behavioral FAIL counts. Mutations affect build-cache copies only."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
 'flash_hud_acquire': [
  ('ignore missing manager', 'if (!manager || g_bNetworkDebugFlag != 0)', 'if (g_bNetworkDebugFlag != 0)'),
  ('test low flag bit', 'if (!manager || g_bNetworkDebugFlag != 0)', 'if (!manager || (g_bNetworkDebugFlag & 1) != 0)'),
  ('wrong timeout', 'sysThread_WaitTimeout(manager->semaphore, -1);', 'sysThread_WaitTimeout(manager->semaphore, 0);'),
  ('lose held flag', '    g_bNetworkDebugFlag = 1;', '    g_bNetworkDebugFlag = 0;'),
  ('report wait failure', '    return 1;\n}', '    return 0;\n}'),
 ],
 'flash_hud_get_group': [
  ('omit diagnostic', 'rage_debugLog("[*** FLASHBASE ERROR ***] Updating without grabbing flash sema!");', '/* diagnostic lost */'),
  ('diagnose locked access', 'loop->manager && g_bNetworkDebugFlag == 0', 'loop->manager && g_bNetworkDebugFlag != 0'),
  ('ignore absent manager', 'loop->manager && g_bNetworkDebugFlag == 0', 'g_bNetworkDebugFlag == 0'),
  ('cache group before callback', '    auto* loop = static_cast<FlashGameLoop*>(g_loop_obj_ptr);\n    if (loop->manager',
   '    void* cached = static_cast<FlashHud*>(hud)->pageGroup;\n    auto* loop = static_cast<FlashGameLoop*>(g_loop_obj_ptr);\n    if (loop->manager'),
 ],
 'flash_hud_release': [
  ('ignore release flag', 'if (manager && g_bNetworkDebugFlag != 0)', 'if (manager)'),
  ('test low release bit', 'if (manager && g_bNetworkDebugFlag != 0)', 'if (manager && (g_bNetworkDebugFlag & 1) != 0)'),
  ('wrong release count', 'sysThread_ReleaseSemaphore(manager->semaphore, 1, nullptr);', 'sysThread_ReleaseSemaphore(manager->semaphore, 2, nullptr);'),
  ('retain held flag', '        g_bNetworkDebugFlag = 0;', '        /* flag clear lost */'),
 ],
}


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/hud_page_group.cpp').read_text()
    caught = 0
    for spec, cases in CASES.items():
        for name, old, new in cases:
            assert source.count(old) == 1, name
            patches = [(old, new)]
            if name == 'cache group before callback':
                patches.append(('return static_cast<FlashHud*>(hud)->pageGroup;', 'return cached;'))
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
