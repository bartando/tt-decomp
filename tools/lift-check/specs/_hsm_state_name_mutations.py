"""Reject name-query ABI and callback reload regressions."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
 ('dirty upper bits', 'static_cast<uint8_t>(static_cast<StateNameManager*>(manager)->CanQueryStateName())', 'static_cast<StateNameManager*>(manager)->CanQueryStateName()'),
 ('ignore index', 'states[stateIndex]->GetName()', 'states[0]->GetName()'),
 ('wrong member offset', 'manager, 8)', 'manager, 4)'),
 ('reverse gate', 'CanQueryStateName()) == 0)', 'CanQueryStateName()) != 0)'),
 ('cache child array', 'if (static_cast<uint8_t>', 'auto* oldStates = rage::load_ptr32<rage::ptr32<NamedState>>(manager, 8);\n    if (static_cast<uint8_t>'),
]


def main():
 source = (Path(__file__).resolve().parents[3]/'src/rage/core/hsm.cpp').read_text()
 for label, old, new in CASES:
  assert old in source, label
  patches=[(old,new)]
  if label == 'cache child array':
   patches.append(('return states[stateIndex]->GetName();', 'return oldStates[stateIndex]->GetName();'))
  out=io.StringIO()
  with contextlib.redirect_stdout(out):
   rc=Checker(Path(__file__).with_name('hsm_context_get_state_name.py'),Options(seed=1,patches=tuple(patches))).run()
  print(f"{'CAUGHT' if rc==1 else 'MISSED'} {label}: {out.getvalue().splitlines()[0]}",flush=True)
  if rc!=1:return 1
 print(f'Caught {len(CASES)}/{len(CASES)} mutations')
 return 0
if __name__=='__main__':raise SystemExit(main())
