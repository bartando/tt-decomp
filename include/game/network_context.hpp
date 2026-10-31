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
