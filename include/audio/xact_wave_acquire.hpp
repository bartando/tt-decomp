#pragma once
#include "rage/ptr32.hpp"
#include <cstdint>

void* msgMsgSink_8D10_g(void* owner, uint32_t index); // @ 0x82448D10
void* xactBank_GetWaveRecord(void* owner, uint32_t index); // @ 0x82448C60
int32_t xactCue_AcquireWave(void* cue); // @ 0x82456D70
int32_t msgMsgSink_EC28_g(void* cue, uint32_t key, rage::ptr32<void>* out, uint32_t unused); // @ 0x8244EC28
