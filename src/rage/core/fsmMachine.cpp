#include "rage/fsmMachine.hpp"
#include <cstdint>

extern "C" void rage_free(void* memory); // @ 0x820C00C0
extern "C" uint8_t fsmMachine_vtable[]; // @ 0x8204DD14
extern "C" uint8_t rage_datBase_vtable[]; // @ 0x820276C4

// @ 0x822227A8 | size: 0x58
void fsmMachine_Destructor_27A8(void* machine) {
    auto* state = static_cast<fsmMachine*>(machine);
    state->m_pVtable = fsmMachine_vtable;
    if (state->m_pStateData) {
        rage_free(state->m_pStateData.get());
        state->m_pStateData = nullptr;
    }
    state->m_pVtable = rage_datBase_vtable;
}
