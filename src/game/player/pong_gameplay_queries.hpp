#pragma once

#include <cstdint>

extern "C" bool pongAnimClip_IsPlaybackReady(void* clip); // @ 0x820D6AA0
extern "C" void pongMatchSettings_GetCourtBounds(void* settings, int sideIndex,
                                                void* lower, void* upper); // @ 0x821C9CD0

struct pongPlayer;
void io_8A48(pongPlayer* player, int32_t* answer); // @ 0x82198A48
