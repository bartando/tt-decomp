#include "rage/float_channel_vtables.hpp"
#include "link/tt_alias.h"

extern "C" void nop_8240E6D0(const char*, ...); // Actual retail blr shared by unused slots.
// A member function pointer is not a code pointer. These declarations name the
// existing Itanium entry symbols with their explicit `this` argument, matching
// this native build's C++ ABI. No adapter body or guessed code address is used.
extern int channelReturnZero(void*) __asm__(TT_ASM_SYMBOL("_ZN4rage16fiAsciiTokenizer5vfn_0Ev")); // @ 0x8210CAF8
extern int staticChannelSize(void*) __asm__(TT_ASM_SYMBOL("_ZN4rage14crAnimDofFloat15GetChannelCountEv")); // @ 0x8216EB20
extern void quantizedChannelEvaluate(void*, void*, float, float*) __asm__(TT_ASM_SYMBOL("_ZN4rage26crAnimChannelQuantizeFloat5vfn_5EPvfPf")); // @ 0x822478E0

namespace rage {
// Exactly 15 entries each. The following image words are RTTI/padding, not slots.
void* g_crAnimChannelStaticFloat_vtable[15] = {
    reinterpret_cast<void*>(crAnimChannel_Delete),
    reinterpret_cast<void*>(crAnimStaticFloat_Place),
    reinterpret_cast<void*>(crAnimStaticFloat_Clone),
    reinterpret_cast<void*>(nop_8240E6D0), reinterpret_cast<void*>(nop_8240E6D0),
    reinterpret_cast<void*>(crAnimStaticFloat_Evaluate),
    reinterpret_cast<void*>(nop_8240E6D0), reinterpret_cast<void*>(nop_8240E6D0),
    reinterpret_cast<void*>(crAnimStaticFloat_Initialize),
    reinterpret_cast<void*>(channelReturnZero), reinterpret_cast<void*>(channelReturnZero),
    reinterpret_cast<void*>(channelReturnZero), reinterpret_cast<void*>(channelReturnZero),
    reinterpret_cast<void*>(staticChannelSize), reinterpret_cast<void*>(crAnimStaticFloat_Serialize),
};
void* g_crAnimChannelRawFloat_vtable[15] = {
    reinterpret_cast<void*>(crAnimRawFloat_Delete),
    reinterpret_cast<void*>(crAnimRawFloat_Place),
    reinterpret_cast<void*>(crAnimRawFloat_Clone),
    reinterpret_cast<void*>(nop_8240E6D0), reinterpret_cast<void*>(nop_8240E6D0),
    reinterpret_cast<void*>(crAnimRawFloat_Evaluate),
    reinterpret_cast<void*>(nop_8240E6D0), reinterpret_cast<void*>(nop_8240E6D0),
    reinterpret_cast<void*>(crAnimRawFloat_Initialize),
    reinterpret_cast<void*>(channelReturnZero), reinterpret_cast<void*>(channelReturnZero),
    reinterpret_cast<void*>(channelReturnZero), reinterpret_cast<void*>(channelReturnZero),
    reinterpret_cast<void*>(crAnimRawFloat_Size), reinterpret_cast<void*>(crAnimRawFloat_Serialize),
};
void* g_crAnimChannelQuantizeFloat_vtable[15] = {
    reinterpret_cast<void*>(crAnimQuantizeFloat_Delete),
    reinterpret_cast<void*>(crAnimQuantizeFloat_Place),
    reinterpret_cast<void*>(crAnimQuantizeFloat_Clone),
    reinterpret_cast<void*>(nop_8240E6D0), reinterpret_cast<void*>(nop_8240E6D0),
    reinterpret_cast<void*>(quantizedChannelEvaluate),
    reinterpret_cast<void*>(nop_8240E6D0), reinterpret_cast<void*>(nop_8240E6D0),
    reinterpret_cast<void*>(crAnimQuantizeFloat_Initialize),
    reinterpret_cast<void*>(channelReturnZero), reinterpret_cast<void*>(channelReturnZero),
    reinterpret_cast<void*>(channelReturnZero), reinterpret_cast<void*>(channelReturnZero),
    reinterpret_cast<void*>(crAnimQuantizeFloat_Size), reinterpret_cast<void*>(crAnimQuantizeFloat_Serialize),
};
}
