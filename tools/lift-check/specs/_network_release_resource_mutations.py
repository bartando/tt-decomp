"""The graphics release bridge must retain the object, data and zero auxiliary."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
def main():
    cases=[('data offset','static_cast<uint8_t*>(self) + 12);','static_cast<uint8_t*>(self) + 8);'),
           ('release data','grc_2CC8(self, data, 0);','grc_2CC8(self, 0, 0);'),
           ('release auxiliary','grc_2CC8(self, data, 0);','grc_2CC8(self, data, 1);')]
    for label,old,new in cases:
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            rc=Checker(Path(__file__).with_name('network_release_resource.py'),Options(trials=64,seed=1,patches=((old,new),))).run()
        print(f"{'CAUGHT' if rc==1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}",flush=True)
        if rc!=1: return 1
    print('Caught 3/3 mutations',flush=True)
    return 0
if __name__=='__main__': raise SystemExit(main())
