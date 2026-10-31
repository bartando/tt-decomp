#pragma once
#include "rage/ptr32.hpp"
#include <cstdint>

struct fsmMachine {
    rage::ptr32<void> m_pVtable;
    uint32_t m_flags;
    rage::ptr32<void> m_pStateData;
};
static_assert(sizeof(fsmMachine) == 12, "fsmMachine retail layout");
void fsmMachine_Destructor_27A8(void* machine); // @ 0x822227A8
