#pragma once
#include <cstdint>
namespace rage {
extern void* g_crAnimChannelStaticFloat_vtable[15]; // @ 0x8204F8D4
extern void* g_crAnimChannelQuantizeFloat_vtable[15]; // @ 0x8204F9AC
extern void* g_crAnimChannelRawFloat_vtable[15]; // @ 0x8204F76C
}
// The image contains these real callback relocations. Missing callback bodies
// remain unresolved at link time; a null slot would conceal missing behavior.
extern "C" {
void* crAnimChannel_Delete(void*, uint32_t flags); // @ 0x82244040
void* crAnimRawFloat_Delete(void*, uint32_t flags); // @ 0x82244180
void* crAnimQuantizeFloat_Delete(void*, uint32_t flags); // @ 0x82244AA0
void crAnimStaticFloat_Place(void*, void* resource); // @ 0x82246578
void crAnimRawFloat_Place(void*, void* resource); // @ 0x822454C8
void crAnimQuantizeFloat_Place(void*, void* resource); // @ 0x82247888
void* crAnimStaticFloat_Clone(void*); // @ 0x82244788
void* crAnimRawFloat_Clone(void*); // @ 0x82244088
void* crAnimQuantizeFloat_Clone(void*); // @ 0x82244A28
void crAnimStaticFloat_Evaluate(void*, void* context, float time, float* value); // @ 0x82246590
void crAnimRawFloat_Evaluate(void*, void* context, float time, float* value); // @ 0x82245520
uint32_t crAnimStaticFloat_Initialize(void*, const float*, uint32_t count, uint32_t stride, float tolerance); // @ 0x822465A0
uint32_t crAnimRawFloat_Initialize(void*, const float*, uint32_t count, uint32_t stride, float tolerance); // @ 0x82245650
uint32_t crAnimQuantizeFloat_Initialize(void*, const float*, uint32_t count, uint32_t stride, float tolerance); // @ 0x822479B0
uint32_t crAnimRawFloat_Size(void*); // @ 0x822461F8
uint32_t crAnimQuantizeFloat_Size(void*); // @ 0x82247B00
void crAnimStaticFloat_Serialize(void*, void* stream); // @ 0x82246600
void crAnimRawFloat_Serialize(void*, void* stream); // @ 0x82245758
void crAnimQuantizeFloat_Serialize(void*, void* stream); // @ 0x82247B10
}
