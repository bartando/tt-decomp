/**
 * rage_misc.cpp — RAGE Engine Miscellaneous Systems
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 * 
 * Implements miniheap allocator and other utility classes.
 */

#include "rage_misc.hpp"
#include <cstdint>

// The original miniheap has three adjacent words (lis -32160, +10248).
// Keep them external so a lifted TU uses the live image state.
extern "C" uint32_t g_miniheapStart;    // @ 0x82602808
extern "C" uint32_t g_miniheapEnd;      // @ 0x8260280C
extern "C" uint32_t g_miniheapCurrent;  // @ 0x82602810

namespace rage {

// ─────────────────────────────────────────────────────────────────────────────
// miniheapAllocator::ScalarDtor() [vtable slot 1 @ 0x823F89B8]
// Allocates memory from the miniheap with alignment
// ─────────────────────────────────────────────────────────────────────────────
void* miniheapAllocator::Allocate(uint32_t size, uint32_t alignment) {
    // Determine alignment mask based on size
    uint32_t alignMask;
    if (size <= 4) {
        alignMask = 3;  // 4-byte alignment
    } else if (size <= 8) {
        alignMask = 7;  // 8-byte alignment
    } else {
        alignMask = alignment - 1;  // Custom alignment
    }
    
    // Align current pointer
    uint32_t aligned = (g_miniheapCurrent + alignMask) & ~alignMask;
    
    // Update current pointer
    uint32_t newCurrent = aligned + size;
    g_miniheapCurrent = newCurrent;
    
    // Check for overflow
    if (newCurrent > g_miniheapEnd) {
        // Call error handler (nop in current implementation)
        // Original: calls function @ 0x8240E6D0 with string @ 0x82074BB4
    }
    
    return reinterpret_cast<void*>(aligned);
}

// ─────────────────────────────────────────────────────────────────────────────
// miniheapAllocator::GetUsedSize [vtable slot 4 @ 0x823F8958]
// Returns current - start (bytes allocated from the miniheap)
// ─────────────────────────────────────────────────────────────────────────────
uint32_t miniheapAllocator::GetUsedSize() const {
    return g_miniheapCurrent - g_miniheapStart;
}

// ─────────────────────────────────────────────────────────────────────────────
// miniheapAllocator::GetFreeSize [vtable slot 5 @ 0x823F8970]
// Returns end - current (bytes remaining in the miniheap)
// ─────────────────────────────────────────────────────────────────────────────
uint32_t miniheapAllocator::GetFreeSize() const {
    return g_miniheapEnd - g_miniheapCurrent;
}

// ─────────────────────────────────────────────────────────────────────────────
// miniheapAllocator::IsInRange [vtable slot 20 @ 0x823F8988]
// Returns true if address falls within the allocated range [start, current)
// ─────────────────────────────────────────────────────────────────────────────
bool miniheapAllocator::IsInRange(uint32_t address) const {
    return (address >= g_miniheapStart) && (address < g_miniheapCurrent);
}

} // namespace rage
