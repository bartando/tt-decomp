#pragma once
#include <cstdint>

extern "C" void* rage_A980(void* device); // @ 0x8235A980 — refill command stream
uint32_t* grc_9B60(void* fixups);           // @ 0x82359B60 — extend fixup chain
int32_t rage_C660(void* device);           // @ 0x8235C660 — submit command stream
extern "C" void rage_EEC0(void* start, void* end); // @ 0x8235EEC0 — flush GPU cache range

extern "C" void rage_A4E0(void* device, uint32_t* gpuAddress, uint32_t* wordCount); // @ 0x8235A4E0
extern "C" void* rage_A8C0(void* device, void* commands, uint32_t gpuAddress,
                           uint32_t wordCount, uint32_t flags, void* fixups); // @ 0x8235A8C0
extern "C" void rage_A780(void* device); // @ 0x8235A780
extern "C" void rage_35A8(void* device, uint32_t flags); // @ 0x823535A8
extern "C" int32_t rage_7BD0(void* device, uint32_t flush, uint32_t mask); // @ 0x82367BD0
