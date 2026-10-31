"""Require behavioral FAIL for deliberately broken control-query lifts."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/player/player_control_queries.cpp"
CASES = [
    ("player_is_controlled", [
        ("drop mode-zero slot comparison", "return at<int32_t>(g_render_obj_ptr, 0x128) == at<int32_t>(player, 0x1D0);", "return 1;"),
        ("allow nonzero practice slot", "if (slot != 0) return 0;", "if (false) return 0;"),
        ("omit practice mode two", "logicMode == 1 || logicMode == 2", "logicMode == 1"),
        ("drop spectator cast", "RTDynamicCast(g_pGameLogic, 0, &g_typeDescriptor_gmLogic,\n                      &g_typeDescriptor_gmLogicSpectator, 0);", "(void)g_pGameLogic;"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    count = 0
    for spec, mutations in CASES:
        for label, old, new in mutations:
            assert old in source, f"missing anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
