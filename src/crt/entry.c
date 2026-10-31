/**
 * entry.c — Xbox 360 CRT entry point and thread context initialization
 * Rockstar Presents Table Tennis (Xbox 360)
 *
 * The game's startup sequence:
 *   __crt_main_entry  (XEX entry, called by the loader)
 *       └─ sysMemAllocator_InitThreadHeap   (init main thread's XTF context)
 *           └─ xe_alloc_thread_ctx_6CA8 (allocate physical thread stack/TLS)
 *       └─ rage_main_stub             (RAGE main loop)
 *
 * The SDA base register (r13) points to a global struct that holds the
 * active memory allocator context at offset +4. sysMemAllocator_InitThreadHeap sets
 * up the main thread's XTF (Xbox Thread Frame) structure so that the heap
 * and TLS allocator are online before game code runs.
 */

#include <stdint.h>
#include <stddef.h>
#include "crt/thread_heap.h"

/* ── Forward declarations ──────────────────────────────────────────── */
int   rage_main_stub(void* parms, void* base);
int   xe_atexit(void (*fn)(void));
void* XePhysicalAlloc_stub(uint32_t sizeBytes, int32_t protectFlags, uint32_t alignment, uint32_t allocFlags);
void  XeTlsBlock_InitStack(struct XeTlsBlock* pXtf, void* stackBase, uint32_t stackSize);
void  XeTlsBlock_BindMainThread(struct XeTlsBlock* pXtf);
void  rage_DebugLog(const char* fmt, ...);

/* ── Globals ───────────────────────────────────────────────────────── */

/* SDA-relative allocator context base — offset +4 holds the
 * active sysMemAllocator vtable pointer. @ 0x82600000 (SDA base) */
extern uint32_t* g_sda_base;                    /* r13-relative */

static const uintptr_t kThreadCtxCtorVtable = 0x82038C4Cu;
static const uintptr_t kThreadAllocFailFmt = 0x82038610u;
static const uint32_t kThreadPhysAllocFlags = 0x20000004u;


/**
 * xe_alloc_thread_ctx_6CA8 @ 0x82186CA8 | size: 0x94
 *
 * Allocates a physical memory block for a thread's execution context
 * (stack + TLS scratch area) and initializes the XeTlsBlock descriptor.
 *
 * @param pXtf      Pointer to the XeTlsBlock to initialize
 * @param stackSize Requested stack size in bytes
 * @param flags     Thread flags (stored at XtfBlock+184)
 */
void xe_alloc_thread_ctx_6CA8(struct XeTlsBlock* pXtf, uint32_t stackSize, uint32_t flags)
{
    /* PPC sequence: addis size,1; addi -1; rlwinm 0,0,15 */
    uint32_t alignedSize = (stackSize + 0xFFFFu) & 0xFFFF0000u;

    pXtf->m_flags = (uint8_t)flags;
    pXtf->m_pad3[0] = 0;
    pXtf->m_stackSz = stackSize;

    pXtf->m_physFlag = pXtf->m_physFlag | 0x80;
    pXtf->m_pVtable = (void*)kThreadCtxCtorVtable;

    void* stackBase = XePhysicalAlloc_stub(alignedSize, -1, 0, kThreadPhysAllocFlags);
    if (stackBase == NULL) {
        rage_DebugLog((const char*)kThreadAllocFailFmt, (int32_t)alignedSize >> 10);
    }

    /* The original always runs XeTlsBlock_InitStack even when allocation fails. */
    XeTlsBlock_InitStack(pXtf, stackBase, alignedSize);
}

/**
 * xe_get_thread_ctx_36E8 @ 0x825836E8 | size: 0x0C
 *
 * atexit callback registered by sysMemAllocator_InitThreadHeap. It forwards the
 * process-global main-thread context object to XeTlsBlock_BindMainThread.
 */
void xe_get_thread_ctx_36E8(void)
{
    XeTlsBlock_BindMainThread(&g_mainThreadXtf);
}


/**
 * sysMemAllocator_InitThreadHeap @ 0x820C0038 | size: 0x88
 *
 * Initializes the main thread's XTF (Xbox Thread Frame) if it hasn't been
 * set up yet. Checks an init flag to guard against double-init. Registers
 * xe_get_thread_ctx_36E8() with xe_atexit() so the context is finalized on exit.
 *
 * The r13 TLS root points to the allocator table; this function installs
 * the default heap address into its active (+4) and saved (+8) slots.
 */
void sysMemAllocator_InitThreadHeap(void)
{
    void** allocCtx = *(void***)g_sda_base;
    if (allocCtx[1] == NULL) {
        if ((g_allocatorInitFlag & 1u) == 0u) {
            g_allocatorInitFlag |= 1u;
            xe_alloc_thread_ctx_6CA8(&g_mainThreadXtf, 0x02C00000u, 0u);
            xe_atexit(xe_get_thread_ctx_36E8);
        }

        allocCtx[1] = &g_mainThreadXtf;
        allocCtx[2] = &g_mainThreadXtf;
    }
}


/**
 * __crt_main_entry @ 0x820C0128 | size: 0x44
 *
 * XEX entry point — called by the Xbox 360 kernel with the startup parms
 * block. Initializes the main thread context then hands off to rage_main.
 *
 * @param pStartupParms  Pointer to the XEX startup parameter block (r3)
 * @param pBase          Module base address passed through from kernel (r4)
 */
void __crt_main_entry(void* pStartupParms, void* pBase)
{
    sysMemAllocator_InitThreadHeap();
    (void)rage_main_stub(pStartupParms, pBase);
}
