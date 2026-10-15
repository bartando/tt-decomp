/**
 * dat_resource_fixup.cpp — relocating a pointer while a resource is placed
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Objects loaded from a resource image run their constructors in place with
 * pointers still holding offsets from the image. While a resource is being
 * placed, the thread's resource context (a TLS slot) describes it; a pointer
 * field inside it is rebased through the context's page table. A pointer
 * field outside it is cleared.
 */

#include <cstdint>

extern "C" uint32_t ke_KeTlsAlloc_623C(void);              // @ 0x8258623C — xboxkrnl KeTlsAlloc
extern "C" void* ke_KeTlsGetValue_621C(uint32_t index);    // @ 0x8258621C — xboxkrnl KeTlsGetValue

extern "C" uint32_t g_datResourceTlsSlot;                 // @ 0x825F5AA8

namespace {

struct datResourceContextView {
    uint32_t m_base;          // +0x00  first byte of the image being placed
    uint32_t m_imageBase;     // +0x04  address the image's pointers are relative to
    uint8_t  m_pad08[0x40];
    uint32_t m_size;          // +0x48
    uint32_t m_pageSize;      // +0x4C
};

datResourceContextView* CurrentResource() {
    if (g_datResourceTlsSlot == 0) {
        g_datResourceTlsSlot = ke_KeTlsAlloc_623C();
    }
    return static_cast<datResourceContextView*>(ke_KeTlsGetValue_621C(g_datResourceTlsSlot));
}

}  // namespace

// @ 0x82121B00 — datResource pointer fixup (ke_1B00)
// The page table is the words from +0x08 on: entry k is the delta for page k.
// The original traps (twi) on a zero page size.
void datResource_PointerFixup(uint32_t* field) {
    datResourceContextView* rsc = CurrentResource();
    if (rsc == nullptr) {
        *field = 0;
        return;
    }
    rsc = CurrentResource();
    const uint32_t at = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(field));
    if (at < rsc->m_base || at > rsc->m_base + rsc->m_size) {
        *field = 0;
        return;
    }
    rsc = CurrentResource();
    const uint32_t value = *field;
    if (value == 0) {
        return;
    }
    const uint32_t page = (value - rsc->m_imageBase) / rsc->m_pageSize;
    *field = reinterpret_cast<const uint32_t*>(rsc)[page + 2] + value;
}
