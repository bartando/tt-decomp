#include "game/ai_swing_direction.hpp"

extern "C" uint32_t g_prngState[2]; // @ 0x825CA2C8
extern "C" const float g_fPrngNormalize; // @ 0x82079E68

// Resolve the AI's four directional flags once. Existing selections bypass
// sampling; opposed directions prefer up over down and right over left.
// @ 0x821A66A8 | size: 0x218
void pongPlayer_66A8_g(aiSwingDirectionView* direction) {
    if (direction->resolved != 0) return;
    for (auto& range : direction->ranges) {
        // Select bits so -0 survives the fsel, then subtract in double.
        // A floating select against literal +0 can fold away its sign.
        uint32_t valueBits, maximumBits;
        __builtin_memcpy(&valueBits, &range.value, 4);
        __builtin_memcpy(&maximumBits, &range.maximum, 4);
        const uint32_t lowerBits = range.value >= 0.0f ? valueBits : 0u;
        float lower;
        __builtin_memcpy(&lower, &lowerBits, 4);
        const uint32_t resultBits = double(lower) - double(range.maximum) >= 0.0
                                      ? maximumBits : lowerBits;
        __builtin_memcpy(&range.value, &resultBits, 4);
    }
    direction->up = 0.0f;
    direction->down = 0.0f;
    direction->right = 0.0f;
    direction->left = 0.0f;
    if (direction->upSelected == 0 && direction->downSelected == 0 &&
        direction->leftSelected == 0 && direction->rightSelected == 0) {
        const uint64_t next = uint64_t(g_prngState[0]) * 0x5CDCFAA7u + g_prngState[1];
        g_prngState[0] = static_cast<uint32_t>(next);
        g_prngState[1] = static_cast<uint32_t>(next >> 32);
        const float sample = float(g_prngState[0] & 0x7FFFFFu) * g_fPrngNormalize;
        const float w0 = direction->upWeight, w1 = direction->downWeight;
        const float w2 = direction->rightWeight, w3 = direction->leftWeight;
        float sum = ((w0 + w1) + w2) + w3;
        if (sum == 0.0f) sum = 1.0f;
        const float scale = 1.0f / sum;
        const float p0 = scale * w0, p1 = scale * w1, p2 = scale * w2;
        if (sample <= p0) {
            direction->upSelected = 1;
        } else if (sample <= p1 + p0) {
            direction->downSelected = 1;
        } else if (sample <= (p2 + p1) + p0) {
            direction->rightSelected = 1;
        } else if (sample <= (__builtin_fmaf(scale, w3, p2) + p1) + p0) {
            direction->leftSelected = 1;
        } else {
            direction->upSelected = 1;
        }
    }
    if (direction->upSelected != 0) direction->up = 1.0f;
    else if (direction->downSelected != 0) direction->down = 1.0f;
    if (direction->rightSelected != 0) direction->right = 1.0f;
    else if (direction->leftSelected != 0) direction->left = 1.0f;
    direction->resolved = 1;
}
