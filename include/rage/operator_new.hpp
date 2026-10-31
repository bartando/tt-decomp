#pragma once
#include <cstdint>

// Retail operator new: initialize thread heap, Allocate(size, 16).
void* rage_Alloc(uint32_t size); // @ 0x820DEC88
