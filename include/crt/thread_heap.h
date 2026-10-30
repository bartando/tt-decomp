#pragma once

#include <stdint.h>

/* Fields touched by the thread-heap constructor (guest layout: 0xC4 bytes). */
struct XeTlsBlock {
    void* m_pVtable;
    void* m_pStackAlign16;
    void* m_pStackRaw;
    uint8_t m_padding0[68];
    uint32_t m_stackSz;
    uint8_t m_padding1[100];
    uint8_t m_flags;
    uint8_t m_pad3[7];
    uint8_t m_physFlag;
};

#ifdef __cplusplus
extern "C" {
#endif
extern struct XeTlsBlock g_mainThreadXtf; /* @ 0x8271B114 */
extern uint32_t g_allocatorInitFlag;     /* @ 0x8271B1D8 */
void sysMemAllocator_InitThreadHeap(void); /* @ 0x820C0038 */
#ifdef __cplusplus
}
#endif
