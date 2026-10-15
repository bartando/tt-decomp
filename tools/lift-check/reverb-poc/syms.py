import json,sys
from pathlib import Path
m=json.load(open(Path(__file__).resolve().parents[3]/'config/434C4803/master_symbol_map.json'))['by_address']
lo=int(sys.argv[1],16); hi=int(sys.argv[2],16)
for a in sorted(m, key=lambda x:int(x,16)):
    v=int(a,16)
    if lo<=v<hi:
        e=m[a]
        print(a, e.get('name'), e.get('type'), e.get('size'))
