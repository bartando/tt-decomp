#include "crt/rtti.h"

// @ 0x8260639C (.data) — current game logic, assigned during mode setup
extern "C" void* g_pGameLogic = nullptr;

// @ 0x825D3758 (.data)
RTTITypeDescriptor g_typeDescriptor_gmLogic = {nullptr, nullptr, ".?AVgmLogic@@"};
// @ 0x825D6FAC (.data)
RTTITypeDescriptor g_typeDescriptor_gmLogicSpectator = {nullptr, nullptr, ".?AVgmLogicSpectator@@"};
