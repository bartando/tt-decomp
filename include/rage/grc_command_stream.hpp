#pragma once
#include <cstdint>

extern "C" void* rage_A980(void* device); // @ 0x8235A980 — refill command stream
uint32_t* grc_9B60(void* fixups);           // @ 0x82359B60 — extend fixup chain
int32_t rage_C660(void* device);           // @ 0x8235C660 — submit command stream
