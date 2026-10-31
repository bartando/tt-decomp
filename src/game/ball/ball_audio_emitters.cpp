// Deferred emitter updates used by ball playback and impact audio.
#include "ball_audio.hpp"
#include <cstdint>
#include <cmath>
#pragma clang fp contract(off)

extern "C" const uint32_t g_affineXYZMask[4]; // @ 0x82619BE0
extern void nop_8240E6D0(const char* format,...); // @ 0x8240E6D0

namespace {
struct EmitterFields {
    uint8_t pad00[0x14];
    uint32_t flags;
    uint8_t pad18[8];
    float gain;
    uint8_t pad24[0x2C];
    float nextPosition[4];
    float currentPosition[4];
};
float CompareLane(uint32_t bits) {
    if ((bits&0x7F800000u)==0) bits&=0x80000000u;
    float value;
    __builtin_memcpy(&value,&bits,4);
    return value;
}
}

// @ 0x82160C98
void BallAudio_SetEmitterPosition(void* emitter,const float* position) {
    auto* fields=static_cast<EmitterFields*>(emitter);
    bool same=true;
    for(int lane=0;lane<4;++lane) {
        uint32_t next,current;
        __builtin_memcpy(&next,position+lane,4);
        __builtin_memcpy(&current,fields->currentPosition+lane,4);
        same &= CompareLane(next&g_affineXYZMask[lane])==CompareLane(current&g_affineXYZMask[lane]);
    }
    if (same) return;
    __builtin_memcpy(fields->nextPosition,position,16);
    fields->flags|=0x80;
}

// @ 0x82162218
void BallAudio_SetEmitterGain(void* emitter,float gain) {
    auto* fields=static_cast<EmitterFields*>(emitter);
    if (__builtin_fabsf(gain-fields->gain)<0.005f) return;
    if (gain<0.0f) {
        nop_8240E6D0("\x1b[33maudControl::SetVolume < 0 attempted\x1b[0m");
        fields->gain=0.0f;
    } else if (gain>1.0f) {
        nop_8240E6D0("\x1b[33maudControl::SetVolume > 1 attempted\x1b[0m");
        fields->gain=1.0f;
    } else {
        fields->gain=gain;
    }
    fields->flags|=1;
}
