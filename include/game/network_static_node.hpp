#pragma once
#include <cstdint>
struct PongNetMessageHolderStaticNode {
    int32_t index;
    const char* name;
    void* next;
};
static_assert(sizeof(void*) != 4 || sizeof(PongNetMessageHolderStaticNode) == 12, "static record image layout");
extern "C" PongNetMessageHolderStaticNode g_holderInstance_1948; // @ 0x825D1948
