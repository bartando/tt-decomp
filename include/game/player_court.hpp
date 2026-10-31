#pragma once
#include <cstdint>

void* pongPlayer_GetCourtBounds(void* table, uint32_t side, void* lower, void* upper,
                                uint32_t variant, uint32_t useProfiles); // @ 0x821EFD20
void pongPlayer_E008_g(void* target, int, int, int side); // @ 0x8219E008
extern "C" void* pongPlayer_E7B0_g(void* target); // @ 0x8219E7B0
