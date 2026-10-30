"""Run behavioral mutations against both specs; patches only touch build copies."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    "game_94f0": ("src/game/template_registry.cpp", [
        ("use argument registry", "(void)registry;  // The original always searches the global registry.", "#define g_templateRegistry (*registry)"),
        ("exclusive lower bound", "searchKey[0] >= entry.field1", "searchKey[0] > entry.field1"),
        ("exclusive upper bound", "searchKey[1] <= entry.field2", "searchKey[1] < entry.field2"),
        ("wrong search direction", "searchKey[1] < entry.field1", "searchKey[0] < entry.field1"),
    ]),
    "rage_find_singleton": ("src/rage/core/rage_core_utils.cpp", [
        ("skip signed pointer check", "static_cast<int32_t>(value) >= 0", "false"),
        ("accept lookup miss", "if (index == -1)\n        return 0;", "if (index == -1)\n        return 1;"),
        ("accept negative offset", "static_cast<int32_t>(offset) < 0", "false"),
        ("wrong cleanup offset", "offset == 32 && value - 32 != 0", "offset == 31 && value - 32 != 0"),
        ("wrong cleanup flags", "0xE0010000u", "0xE001u"),
        ("omit removal", "datResourceMgr_RemoveEntry(base);", "(void)base;"),
    ]),
}


def main():
    for spec, (source_path, mutations) in CASES.items():
        source = (ROOT / source_path).read_text()
        caught = 0
        for name, old, new in mutations:
            assert source.count(old) == 1, name
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=256, seed=1, patches=((old, new),))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            caught += 1
        print(f"{spec}: caught {caught}/{len(mutations)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
