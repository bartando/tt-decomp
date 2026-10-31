#pragma once
#include <cstdint>

extern "C" {
void cmOperator_ClearName(void* node); // @ 0x8223A258
void cmOperator_SetPrimaryName(void* node, const char* name, int copy); // @ 0x8223A2E8
void cmOperator_SetSecondaryName(void* node, const char* text, uint32_t copy); // @ 0x8223A370
void cmOperator_SetIntegerValue(void* node, int32_t value); // @ 0x8223A410
void cmOperator_SetRealValue(void* node, float value); // @ 0x8223A488
void cmOperator_SetBooleanValue(void* node, uint32_t value); // @ 0x8223A500
// Return a four-byte pointer slot; growth is fixed at 16, ignoring r4.
void* atFreeList_Alloc(void* array, uint32_t unusedR4); // @ 0x822665C0
void cmOperator_SetInt(void* owner, const char* name, int value, uint32_t copyName); // @ 0x822395F0
// LTCG leaves an unused integer slot in r5 and takes copyName in r6.
void cmOperator_SetFloat(void* owner, const char* name, uint32_t unusedR5, uint32_t copyName, float value); // @ 0x82239698
}
