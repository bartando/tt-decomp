#pragma once
#include <stdint.h>

using phElementConstructor = void (*)(void*);

// MSVC vector-constructor iterator: count in r5, callback in r6.
void phJoint3Dof_0170_g(void* destination, int32_t stride, int32_t count,
                      phElementConstructor constructor); // @ 0x820C0170
void atSingleton_E3F0_p44(void* object); // @ 0x8225E3F0
void util_4628(void* block); // @ 0x82154628

// Typed constructor use of the existing retail no-op, rather than a data pointer.
void nop_8240E6D0(void* object); // @ 0x8240E6D0
