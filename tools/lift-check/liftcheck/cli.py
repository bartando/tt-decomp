"""lift-check <spec> [--trials N] [--seed S] [--ftol X]   |   lift-check all [--jobs N]
[--filter PREFIX]   |   lift-check selftest"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SPECS = Path(__file__).resolve().parent.parent / "specs"


def find_spec(name: str) -> Path:
    p = Path(name)
    if p.exists():
        return p
    for cand in (SPECS / name, SPECS / f"{name}.py"):
        if cand.exists():
            return cand
    raise SystemExit(f"lift-check: no spec '{name}' (looked in {SPECS})")


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["selftest"]:
        from .selftest import main as selftest
        return selftest(argv[1:])
    if argv[:1] == ["all"]:
        from .batch import main as run_all
        return run_all(argv[1:])
    ap = argparse.ArgumentParser(prog="lift-check", description=__doc__)
    ap.add_argument("spec", nargs="+", help="spec file or name in tools/lift-check/specs/")
    ap.add_argument("--trials", type=int, help="random trials (default: spec TRIALS or 200)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ftol", type=float, help="relative float tolerance (default: spec FTOL or 0)")
    ap.add_argument("--opt", default="-O2", help="clang optimisation level for the lift")
    ap.add_argument("--fp-contract", choices=("on", "off", "fast"),
                    help="fuse a*b+c into fmadd (default: spec FP_CONTRACT or on)")
    ap.add_argument("--source", help="compile this file instead of the spec's SOURCE")
    ap.add_argument("--only", type=int, metavar="N", help="run just trial N (with -v: dump both sides)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    from .build import BuildError
    from .runner import Checker, Options

    worst = 0
    for name in args.spec:
        path = find_spec(name)
        opts = Options(trials=args.trials, seed=args.seed, ftol=args.ftol, opt=args.opt,
                       source=args.source, verbose=args.verbose, only=args.only,
                       fp_contract=args.fp_contract)
        try:
            rc = Checker(path, opts).run()
        except BuildError as e:
            print(f"BUILD {path.stem}: {e}")
            rc = 2
        worst = max(worst, rc)
    return worst
