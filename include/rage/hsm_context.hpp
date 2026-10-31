#pragma once
#include <cstdint>

// @ 0x822228B8. Queries slot 6, then the indexed child's name (slot 13).
const char* hsmContext_GetStateName(void* manager, uint32_t stateIndex);
