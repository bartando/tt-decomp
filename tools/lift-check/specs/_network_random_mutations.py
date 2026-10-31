"""Shuffled generator, inclusive range and packed candidate selection guards."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
RANDOM='src/rage/math/random_range.cpp'
SELECT='src/game/network/network_selection.cpp'
CASES={
 'network_random_next':(RANDOM,[
  ('multiplier','*seed * 0x7FFFFFEDu','*seed * 0x7FFFFFEBu'),
  ('seed transition','*seed = second;','*seed = first;'),
  ('shuffle mask','second & 0x7F','second & 0x3F'),
  ('shuffle replacement','g_randomShuffleTable[index] = first;','g_randomShuffleTable[index] = second;'),
 ]),
 'network_random_range':(RANDOM,[
  ('equal range','uint32_t high) {\n    if (low == high) return low;','uint32_t high) {\n    if (low == high) return low + 1;'),
  ('inclusive bound','width = high - low + 1u;','width = high - low;'),
  ('seed offset','uint32_t high) {\n    if (low == high) return low;\n    auto* seed = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(owner) + 0xAC);','uint32_t high) {\n    if (low == high) return low;\n    auto* seed = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(owner) + 0xA8);'),
 ]),
 'network_random_range_signed':(RANDOM,[
  ('inclusive signed bound','static_cast<uint32_t>(low) + 1u;','static_cast<uint32_t>(low) + 2u;'),
 ]),
 'network_select_candidate':(SELECT,[
  ('packed count','*reinterpret_cast<uint32_t*>(inner) & 0xFFFF','*reinterpret_cast<uint32_t*>(inner) >> 16'),
  ('lower boundary','bounds[0] <= value','bounds[0] < value'),
  ('upper boundary','bounds[1] >= value','bounds[1] > value'),
  ('random owner','rage::load_ptr32<void>(holder, 4)','static_cast<void*>(reinterpret_cast<uint8_t*>(holder) + 4)'),
  ('chosen payload','entries + slot * 16);','entries + slot * 16 + 4);'),
 ]),
}
def main():
    root=Path(__file__).resolve().parents[3]
    total=0
    for spec,(path,mutations) in CASES.items():
        source=(root/path).read_text()
        for label,old,new in mutations:
            assert source.count(old)==1,(spec,label,source.count(old))
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=192,seed=1,patches=((old,new),))).run()
            print(f"{spec}: {'CAUGHT' if rc==1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}",flush=True)
            if rc!=1:
                print(output.getvalue())
                return 1
            total+=1
    print(f'Caught {total}/{total} mutations',flush=True)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
