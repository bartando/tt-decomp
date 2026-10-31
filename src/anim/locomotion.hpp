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

// The lookup takes the full ID word; its direct store/search narrows to 16 bits.
// @ 0x821D04F0
bool LocomotionStateAnim_04F0_g(void* data, uint32_t id, uint16_t* index);

// Indexed channel weight; type is narrowed to a byte inside the function.
// @ 0x822481A8
uint32_t LocomotionStateAnim_81A8(void* self, uint32_t type, uint32_t id,
                                 void* userdata, float* weight);

// Evaluate the entry at its saved phase, advance it and return the new phase.
// @ 0x820C2858
float LocomotionStateAnim_2858(void* entry, void* frame, uint32_t unusedR5);

// Advance and wrap one animation entry's normalized phase.
// @ 0x820C28B0
void LocomotionStateAnim_28B0_w(void* entry);
