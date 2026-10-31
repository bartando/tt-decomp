"""Behavioral checks for round-robin reset, FSM teardown and partial shot init."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES = {
    'network_round_robin_match_reset': ('src/game/network/round_robin_state.cpp', [
        ('preserved flags', 'bytes[29] &= 0x3F;', 'bytes[29] &= 0x7F;'),
        ('score default', 'bytes[27] = 1;', 'bytes[27] = 0;'),
        ('cleared range', 'bytes + 7, 0, 20', 'bytes + 7, 0, 19'),
    ]),
    'network_round_robin_reset': ('src/game/network/round_robin_state.cpp', [
        ('match count', 'int i = 27; i >= 0;', 'int i = 26; i >= 0;'),
        ('reset identifier', 'entry[4] = 0xFF;', 'entry[4] = 0;'),
    ]),
    'network_round_robin_init': ('src/game/network/round_robin_state.cpp', [
        ('player count', 'state->playerCount = 4;', 'state->playerCount = 8;'),
        ('round count', 'round < 7;', 'round < 6;'),
        ('match identifier', 'entry[4] = static_cast<uint8_t>(index);', 'entry[4] = static_cast<uint8_t>(index + 1);'),
    ]),
    'network_fsm_destroy': ('src/rage/core/fsmMachine.cpp', [
        ('derived vtable', 'state->m_pVtable = fsmMachine_vtable;', '(void)state;'),
        ('release', 'rage_free(state->m_pStateData.get());', '(void)state->m_pStateData;'),
        ('clear ownership', 'state->m_pStateData = nullptr;', '(void)state;'),
        ('base vtable', 'state->m_pVtable = rage_datBase_vtable;', '(void)state;'),
    ]),
    'network_shot_initialize': ('src/game/ball/ball_shot_initialize.cpp', [
        ('unused vector', 'shot->v30[0] = {};', 'shot->v30[0] = {}; shot->v30[1] = {};'),
        ('vector w', 'shot->v50.x = shot->v50.y = shot->v50.z = 0.0f;', 'shot->v50 = {};'),
        ('shot flags', 'shot->hB2 = 0xFFFF;', 'shot->hB2 = 0;'),
        ('loaded default', 'shot->f70[5] = g_floatConstant4;', 'shot->f70[5] = -11.85f;'),
    ]),
}
def main():
    root=Path(__file__).resolve().parents[3]
    total=0
    for spec,(path,mutations) in CASES.items():
        source=(root/path).read_text()
        for label,old,new in mutations:
            assert source.count(old)==1,(spec,label)
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=128,seed=1,patches=((old,new),))).run()
            print(f"{spec}: {'CAUGHT' if rc==1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}",flush=True)
            if rc!=1:
                print(output.getvalue())
                return 1
            total+=1
    print(f'Caught {total}/{total} mutations',flush=True)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
