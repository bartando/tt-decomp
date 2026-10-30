#pragma once

#include <cstdint>

// Evaluate a clip bundle into a frame; r4 is unused in the original.
// @ 0x822488E0
bool LocomotionStateAnim_88E0_g(void* bundle, void* unusedR4, void* frame,
                               uint32_t integralFrames, uint32_t flags, float time);

// Forward a channel blend operation to its virtual slot 7.
// @ 0x8224BB98
void LocomotionStateAnim_BB98(void* entry, void* source, float weight,
                             uint32_t unusedR5, uint32_t flags);
