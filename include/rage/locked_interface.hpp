#pragma once
#include <cstdint>

// Retain the interface through its AddRef virtual while holding the shared lock.
uint32_t phObject_AddRefLocked(void* object); // @ 0x82460850
