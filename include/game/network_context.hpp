#pragma once
#include <cstdint>

// Drain the component's active-node chain, then reset counts and indices.
void UpdateNetworkState(void* component); // @ 0x823D2BE8
// Acquire the loop's guarded context, returning one only on a new acquisition.
// The retail entry ignores its r3 argument.
uint8_t PollButtonState(void* unused); // @ 0x822EB2A8
// Check the access guard and return the pointer at context + 0x5C.
void* GetNetworkClient(void* context); // @ 0x822EB1E8
// Release the loop's guarded context when held; r3 is unused in retail.
void InitiateConnection(void* unused); // @ 0x822EB320

// Fixed pool used by the component reset at 0x823D2BE8. Pointer fields widen on
// native hosts; all pool operations use these shared members and array strides.
struct NetworkContextNode {
    int32_t field_00;
    int32_t field_04;
    uint32_t field_08;
    uint32_t field_0C;
    NetworkContextNode* activeNext; // +0x10 in retail
    uint16_t previousFree;         // +0x14
    uint16_t nextFree;             // +0x16
};
struct NetworkContextPool {
    NetworkContextNode nodes[50];
    uint16_t freeCount;             // +0x4B0
    uint16_t field_4B2;
    uint16_t freeTail;              // +0x4B4
    uint8_t _pad4B6[10];
    NetworkContextNode* activeHead; // +0x4C0
    uint32_t field_4C4;
    uint32_t activeCount;           // +0x4C8
    uint16_t field_4CC;
    uint16_t field_4CE;
    uint8_t _pad4D0[0x1F8];
    uint16_t currentIndex;          // +0x6C8
};
void networkContextReleaseNode(NetworkContextPool* pool, NetworkContextNode* node); // @ 0x823D2E00
