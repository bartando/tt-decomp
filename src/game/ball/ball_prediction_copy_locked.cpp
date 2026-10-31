#include "ball_predict.hpp"

bpShot* ballPredict_CopyShot(bpShot* destination, const bpShot* source); // @ 0x821E6470
void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0

// Despite its old name, this copies an entire prediction shot into the
// context's embedded buffer. +0x104 is the unlocked flag; +0x105 enables it.
// @ 0x82287040 | size: 0x88
void CopyVectorThreadSafe(void* destination, void* source) {
    auto* context = static_cast<uint8_t*>(destination);
    if (context[0x105] != 0) {
        context[0x104] = 0;
    } else {
        nop_8240E6D0("Cannot Lock when Unlock is not enabled");
    }
    ballPredict_CopyShot(reinterpret_cast<bpShot*>(context + 0x40),
                         static_cast<const bpShot*>(source));
    if (context[0x105] != 0) {
        context[0x104] = 1;
    } else {
        nop_8240E6D0("Cannot Lock when Lock is not enabled");
    }
}
