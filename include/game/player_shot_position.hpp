#pragma once
#include <cstdint>

void* pongPlayer_ComputeTargetPosition(void* output, void* entry, uint32_t force); // @ 0x821D6470
void playerShotEntry_UpdatePositionWithOffsets(void* entry, uint32_t force); // @ 0x821D62A8
void playerShotEntry_UpdatePositionWithOffset(void* entry); // @ 0x821D6308
