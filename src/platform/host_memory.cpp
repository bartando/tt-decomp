#include "xam/kernel.h"
#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <unordered_map>

namespace {
struct Allocation { uint32_t size, protect; };
std::mutex allocationMutex;
std::unordered_map<void*, Allocation> allocations;
}
// This port uses host addresses, not a guest physical-address reservation.
// Explicit address ranges and read-only/device-specific protections cannot be
// satisfied by aligned heap storage and therefore fail rather than being ignored.
extern "C" void* MmAllocatePhysicalMemoryEx(uint32_t flags, uint32_t size, uint32_t protect,
                                           uint32_t minimum, uint32_t maximum, uint32_t alignment) {
    if (flags > 2 || !size || minimum || maximum != UINT32_MAX || (protect & 0xFFu) != 4) return nullptr;
    if (protect & ~(0xFFu | 0x200u | 0x400u | 0x20000000u | 0x10000000u)) return nullptr;
    uint64_t page = protect & 0x10000000u ? 0x1000000u : protect & 0x20000000u ? 0x10000u : 0x1000u;
    if (alignment && (alignment & (alignment - 1))) return nullptr;
    uint64_t rounded = (uint64_t(size) + page - 1) & ~(page - 1);
    if (rounded > UINT32_MAX) return nullptr;
    void* result = nullptr;
    if (posix_memalign(&result, std::max<uint64_t>(alignment, page), rounded)) return nullptr;
    std::memset(result, 0, rounded);
    try {
        std::lock_guard<std::mutex> guard(allocationMutex);
        allocations.emplace(result, Allocation{static_cast<uint32_t>(rounded), protect});
    } catch (...) { std::free(result); return nullptr; }
    return result;
}
extern "C" void MmFreePhysicalMemory(uint32_t, void* address) {
    std::lock_guard<std::mutex> guard(allocationMutex);
    auto it = allocations.find(address);
    if (it == allocations.end()) return;
    allocations.erase(it);
    std::free(address);
}
extern "C" uint32_t MmQueryAllocationSize(void* address) {
    std::lock_guard<std::mutex> guard(allocationMutex);
    auto it = allocations.find(address);
    return it == allocations.end() ? 0 : it->second.size;
}
