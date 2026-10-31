#pragma once
#include <cstdint>
#include <cstddef>

struct aiSwingDirectionView {
    uint8_t unused00[4];
    float up, down, right, left;         // +0x04
    uint8_t unused14[8];
    float upWeight, downWeight;         // +0x1C
    uint8_t unused24[8];
    float rightWeight, leftWeight;      // +0x2C
    struct Range { float value, maximum; } ranges[4]; // +0x34
    uint8_t downSelected, upSelected, leftSelected, rightSelected; // +0x54
    uint8_t resolved;                   // +0x58
};
static_assert(offsetof(aiSwingDirectionView, ranges) == 0x34, "AI direction ranges");
static_assert(offsetof(aiSwingDirectionView, resolved) == 0x58, "AI resolved flag");
void pongPlayer_66A8_g(aiSwingDirectionView* direction); // @ 0x821A66A8
