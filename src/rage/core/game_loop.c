/**
 * rage/game_loop.c — Subsystem and audio initialisation for the game loop
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Covers:
 *   rage_subsystem_init  — Allocates Xbox thread semaphores and registers
 *                          the main game thread with the RAGE scheduler.
 *   audSystem_init       — Walks a null-terminated list of audio-device
 *                          path strings, builds full file-system paths, and
 *                          opens each device via fiDevice_GetDevice.
 */

#include "rage/rage_system.hpp"
#include "rage/fi_stream.hpp"
/* audio_system.hpp removed: C file needs no C++ headers */
#include <stdint.h>
#include <string.h>
extern void*    g_game_obj_ptr;
extern void     sysMemAllocator_InitThreadHeap(void);  /* @ 0x820C0038 */

#include <stdio.h>   /* _snprintf */

// ---------------------------------------------------------------------------
// External declarations
// ---------------------------------------------------------------------------

// Xbox thread / synchronisation primitives (XAM layer)
// xam_CreateEvent — Creates a kernel event object via NtCreateEvent.
//   r3=type?, r4=initialCount, r5=maxCount, r6=flags → returns handle
extern void* xam_CreateEvent(uint32_t type, uint32_t initCount,
                             uint32_t maxCount, uint32_t flags); // @ 0x82566C88

// RAGE kernel thread registration.
// r3=func, r4=param, r5=stack_size, r6=base_priority_delta,
// r7=name_fmt_str, r8=start_suspended, r9=processor_affinity
// Returns the kernel thread handle (or 0/-1 on failure).
extern uint32_t rage_RegisterThread(void* func, void* param,
                                          uint32_t stackSize,
                                          uint32_t basePriorityDelta,
                                          void* nameFmt,
                                          uint32_t startSuspended,
                                          uint32_t processorAffinity); // @ 0x82187FD0


// Debug log — no-op (blr) in release builds; fires on guard failures.
extern void rage_DebugLog(const char* msg, ...);  // @ 0x8240E6D0

// Globals

// g_semRender, g_semUpdate, g_semIO — three XAM kernel semaphore handles
// Stored at r31+26104/26108/26112 where r31 = lis(-32160) = 0x82600000
extern void* g_semRender;   /* @ 0x826065F8 — native opaque handle, as defined in globals.c */
extern void* g_semUpdate;   /* @ 0x826065FC */
extern void* g_semIO;       /* @ 0x82606600 */

// g_mainThreadHandle — kernel handle for the RAGE main-loop scheduler thread
extern uint32_t g_mainThreadHandle;  /* @ 0x825D0078 */

// rage_GameLoopThreadEntry — RAGE main-loop scheduler thread entry function.
// Loops calling vtable[2] (DoFrame) then vtable[1] (WaitVSync) on the
// root game object, driving the main update/render cadence.
extern void rage_GameLoopThreadEntry(void* gameObjPtr);  /* @ 0x822E2598 */

// Subsystem init debug strings (.rdata, release no-ops via rage_DebugLog)
extern const char k_subsysInitErrFmt[];   /* @ 0x8205A30C */
extern const char k_rageThreadNameFmt[];  /* @ 0x8205A340 — debug thread name */


// ===========================================================================
// rage_subsystem_init  @ 0x822E2430 | size: 0xDC
//
// Initialises the three RAGE scheduler semaphores and registers the RAGE
// main-loop scheduler thread (rage_GameLoopThreadEntry @ 0x822E2598).
//
// Step 1: Guard — aborts (with debug log) if g_game_obj_ptr is null.
//         The root game object must be created before subsystems can init.
//
// Step 2: Allocate three XAM kernel semaphores via xam_CreateEvent:
//           g_semRender (0x826065F8): type=0, init=1, max=0, flags=0
//           g_semUpdate (0x826065FC): type=0, init=1, max=0, flags=0
//           g_semIO     (0x82606600): type=0, init=1, max=1, flags=0
//         NOTE: max=0 for render/update (binary semaphores), max=1 for IO.
//
// Step 3: Register the RAGE main-loop scheduler thread:
//           func   = rage_GameLoopThreadEntry (game-loop scheduler)
//           param  = g_game_obj_ptr     (startup arg: root game object)
//           stack  = 0x18000 (98304 bytes)
//           basePriorityDelta = 8  → KeSetBasePriorityThread(h, 8-8=0)
//           nameFmt = k_rageThreadNameFmt (debug name, no-op in release)
//           startSuspended = 1   → thread starts suspended
//           processorAffinity = 0 → run on processor 0
//         Handle stored to g_mainThreadHandle @ 0x825D0078.
//
// Key globals (all at lis(-32160)+offset, base=0x82600000):
//   g_game_obj_ptr @ 0x82606604  — root game object pointer (guard + thread param)
//   g_semRender    @ 0x826065F8  — render semaphore handle
//   g_semUpdate    @ 0x826065FC  — update semaphore handle
//   g_semIO        @ 0x82606600  — IO semaphore handle
// ===========================================================================
void rage_subsystem_init(void) {
    // Guard: root game object must exist.
    if (g_game_obj_ptr == NULL) {
        rage_DebugLog(k_subsysInitErrFmt);
        return;
    }

    // Allocate render semaphore: binary (max=0), starts signalled (init=1).
    g_semRender = xam_CreateEvent(0, 1, 0, 0);

    // Allocate update semaphore: binary (max=0), starts signalled (init=1).
    g_semUpdate = xam_CreateEvent(0, 1, 0, 0);

    // Allocate IO semaphore: counting (max=1), starts signalled (init=1).
    g_semIO = xam_CreateEvent(0, 1, 1, 0);

    // Register the RAGE main-loop scheduler thread.
    g_mainThreadHandle = rage_RegisterThread(
        (void*)rage_GameLoopThreadEntry, /* r3: thread entry function             */
        (void*)g_game_obj_ptr,     /* r4: startup param = root game object  */
        98304u,                    /* r5: stack size = 0x18000              */
        8u,                        /* r6: base priority delta (8-8=0)       */
        (void*)k_rageThreadNameFmt,/* r7: debug thread name fmt             */
        1u,                        /* r8: start suspended                   */
        0u                         /* r9: processor affinity = CPU 0        */
    );
}

// ===========================================================================
// audSystem_init_1ED0  @ 0x82221ED0 | size: 0x18C
//
// Opens the audio render-output device ("RN_OUT") then mounts each component
// path in the audio-device table.
//
// The audio-device table (g_audPathTable @ 0x825D1D40, 96 bytes) is an array
// of 12 eight-byte records:
//
//   struct AudPathRecord {
//       const char* m_pPath;   // +0  — path string; NULL ends iteration
//       uint32_t    m_fHasMore;// +4  — non-null means at least one more entry
//   };
//
// For each non-empty entry:
//   1. Build fullPath:     snprintf(buf, 256, g_audPathFmt,  "RN_OUT", entry)
//   2. Build strippedPath: snprintf(buf, 256, g_audPathFmt2, "RN_OUT", entry)
//   3. pos = strlen(strippedPath)   ← prefix length
//   4. Inner loop — walk fullPath from pos, split on '\\':
//        a. Copy chars fullPath[pos..pos+n] to strippedPath[pos..pos+n]
//           until '\\' or '\0' is found.
//        b. Null-terminate strippedPath[pos+n].
//        c. device->vtable[10](device, strippedPath)  ← mount this component.
//        d. Restore strippedPath[pos+n] = '\\'.
//        e. pos += n + 1 (skip the backslash).
//        f. Repeat until fullPath[pos] == '\0'.
//
// Key globals:
//   g_audPathTable   @ 0x825D1D40  — 12-entry AudPathRecord array
//   k_audBasePath    @ 0x8204DAA4  — "RN_OUT"  (14 bytes incl. null)
//   k_audPathFmt     @ 0x82027434  — format1: "%s%s" or similar (6 bytes)
//   k_audPathFmt2    @ 0x8204DBFC  — format2: "NameChant" label (4 bytes)
// ===========================================================================

// Entry in the audio-device path table (8 bytes each, 12 entries @ 0x825D1D40).
typedef struct AudPathRecord {
    const char* m_pPath;    /* +0 — path string pointer; NULL = end of list */
    uint32_t    m_fHasMore; /* +4 — non-null means successor entry exists   */
} AudPathRecord;

extern AudPathRecord g_audPathTable[12]; /* @ 0x825D1D40 */
extern const char    k_audBasePath[];    /* "RN_OUT"     @ 0x8204DAA4 */
extern const char    k_audPathFmt[];     /* path format1 @ 0x82027434 */
extern const char    k_audPathFmt2[];    /* path format2 @ 0x8204DBFC */

// Virtual-call helper: fiDevice::Mount (vtable slot 10, byte offset 40)
typedef int (*fiDevice_MountFn)(struct fiDevice*, const char*);
#define fiDevice_Mount(dev, path) \
    ((fiDevice_MountFn)(*(void***)(dev))[10])((dev), (path))

void audSystem_init(void)
{
    // Open the base audio output device ("RN_OUT").
    struct fiDevice* device = fiDevice_GetDevice(k_audBasePath, 1);

    // First-entry guard: if the first record has no successor, bail.
    if (g_audPathTable[0].m_fHasMore == 0)
        return;

    // Walk each path record in the table.
    for (int i = 0; g_audPathTable[i].m_pPath != NULL; ++i) {
        const char* entry = g_audPathTable[i].m_pPath;

        // Measure path length; skip empty entries.
        int elen = 0;
        while (entry[elen]) elen++;
        if (elen == 0)
            continue;

        // Build the two formatted path buffers on the stack.
        char strippedPath[256];   /* sp+80  in original frame  */
        char fullPath[256];       /* sp+336 in original frame  */
        snprintf(fullPath,     sizeof(fullPath),     k_audPathFmt,  k_audBasePath, entry);
        snprintf(strippedPath, sizeof(strippedPath), k_audPathFmt2, k_audBasePath, entry);

        // pos starts at end of the prefix (strippedPath's filled length).
        int pos = 0;
        while (strippedPath[pos]) pos++;

        // Inner loop: split fullPath on '\\' from position pos onward,
        // mounting each component via the device vtable.
        // Assembly: loc_82221FB8 — loc_82222040.
        for (;;) {
            // Copy chars from fullPath[pos..] into strippedPath[pos..]
            // until we hit '\\' or '\0'.
            int start = pos;
            for (;;) {
                char c = fullPath[pos];
                if (c == '\\' || c == '\0')
                    break;
                strippedPath[pos] = c;   /* stbx r10, r8, r11 (r8 = sp+80-sp+336 = -256) */
                pos++;
            }

            // Null-terminate and mount this component path.
            strippedPath[pos] = '\0';
            fiDevice_Mount(device, strippedPath);

            // Restore the backslash separator and advance past it.
            strippedPath[pos] = '\\';
            char next = fullPath[pos];   /* lbzx r7, r31, r8 — char AT pos */
            pos++;                        /* addi r31, r31, 1  */

            // Stop when we've consumed the full path.
            if (next == '\0')
                break;
        }

        // Advance to next record and check the "has more" flag.
        // (The loop condition re-evaluates g_audPathTable[i].m_pPath.)
    }
}



// ===========================================================================
// pgStreamer_Init  @ 0x820F8A00 | size: 0xFC
//
// Initialises the pgStreamer asynchronous streaming pool and starts the
// pgStreamer background reader thread (DestroyPageGroup).
//
// This function lives in the pgStreamer compilation unit, immediately between
// pgStreamer_Close (0x820F88F8) and pgStreamer_Drain (0x820F8B00) in the
// binary layout.  The name "grcDevice_init_8A00" from the call-tree doc was
// a provisional label; the true subsystem is the pgStreamer asset streamer.
//
// Steps:
//  1. Stamp pool capacity (256) into g_pgStreamerPool.capacity.
//  2. Ensure the main-thread heap context is live (sysMemAllocator_InitThreadHeap).
//  3. Allocate the backing pool via the RAGE sysMemAllocator vtable slot 1:
//       Alloc(size=0xA000, align=16)  →  256 × 160 bytes = 40 960 bytes.
//  4. Build a singly-linked free list across all 256 nodes:
//       node[+0]  = i             (self-index)
//       node[+4]  = 0xFFFFFFFF   (free sentinel)
//       node[+16] = i + 1        (next-free; 256 = end-of-list)
//  5. Reset freeHead = 0 (all nodes free, head at slot 0).
//  6. If g_pgThreadInitGate is unarmed, register DestroyPageGroup as a background
//     kernel thread:
//       stack  = 65 536 bytes (0x10000)
//       base-priority delta = 6  →  KeSetBasePriorityThread(h, 8-6=2)
//       processor = 0  →  XSetThreadProcessor(h, 0)
//
// Key globals:
//   g_pgStreamerPool.capacity @ 0x825EB26C  — written here (256)
//   g_pgStreamerPool.freeHead @ 0x825EB270  — written here (0)
//   g_pgStreamerPool.pMemory  @ 0x825EB274  — written here (alloc ptr)
//   g_pgQueue                @ 0x82607AA8  — 16-slot ring + semaphores (408 B)
//                                             (used by DestroyPageGroup via SDA)
//   g_pgThreadInitGate       @ 0x825CA074  — RTTI-gate; m_pName != NULL → skip
//   k_pgThreadNameFmt        @ 0x8202FB00  — "%s" thread name format
// ===========================================================================

// Three adjacent .data symbols form the pool descriptor:
//   lbl_825EB25C (20 B) — stats header (touched by pgStreamer_ProcessEntry)
//     +0x10 of that symbol = capacity field below
//   lbl_825EB270 (4 B)  — freeHead
//   lbl_825EB274 (8 B)  — pMemory + padding
// We model just the three fields this function writes:
typedef struct pgStreamerPool {
    uint32_t capacity;   /* @ 0x825EB26C — always 256 */
    uint32_t freeHead;   /* @ 0x825EB270 — head of free list */
    void*    pMemory;    /* @ 0x825EB274 — backing allocation */
} pgStreamerPool;

extern pgStreamerPool g_pgStreamerPool;  /* anchored at 0x825EB26C */

// Gate: non-null m_pName = thread already registered
typedef struct {
    uint32_t m_vftable;
    uint8_t* m_pName;
} pgThreadInitGate;
extern pgThreadInitGate g_pgThreadInitGate;  /* @ 0x825CA074 */

extern void           DestroyPageGroup(void);        /* pgStreamer reader thread @ 0x820F8250 */
extern const char     k_pgThreadNameFmt[];    /* "%s" @ 0x8202FB00 */

void pgStreamer_Init(void)
{
    g_pgStreamerPool.capacity = 256;

    // Ensure the main-thread allocator heap is ready.
    sysMemAllocator_InitThreadHeap();

    // Allocate backing pool: 256 nodes × 160 bytes = 0xA000 bytes, 16-byte aligned.
    // VCALL: allocObj = *(g_sda_base[0] + 4);  call allocObj->vtable[1](size, align)
    extern uint32_t* g_sda_base;
    uint32_t* allocRoot = (uint32_t*)(uintptr_t)g_sda_base[0];
    void*     allocObj  = (void*)(uintptr_t)allocRoot[1];
    typedef void* (*AllocFn)(void*, uint32_t, uint32_t);
    AllocFn   allocFn   = ((AllocFn*)*(void**)allocObj)[1];
    void*     pool      = allocFn(allocObj, 0xA000u, 16u);
    g_pgStreamerPool.pMemory = pool;

    // Build free list: node stride = 160 bytes.
    uint8_t* base = (uint8_t*)pool;
    for (int i = 0; i < 256; ++i) {
        uint8_t* node = base + (uint32_t)i * 160u;
        *(uint32_t*)(node +  0) = (uint32_t)i;       /* own index (0-255)    */
        *(uint32_t*)(node +  4) = 0xFFFFFFFFu;       /* free sentinel        */
        *(uint32_t*)(node + 16) = (uint32_t)(i + 1); /* next (256 = end)     */
    }
    g_pgStreamerPool.freeHead = 0;

    // Register the reader thread if not already started.
    // r4 = 0 at the call site (result of gate-null clrlwi left 0 in r4).
    // The thread uses g_pgQueue (SDA global) rather than a startup param.
    if (g_pgThreadInitGate.m_pName == NULL) {
        rage_RegisterThread(
            (void*)DestroyPageGroup,         /* r3: thread function                */
            NULL,                     /* r4: startup param (0 — uses SDA)  */
            65536u,                   /* r5: stack size = 0x10000           */
            6u,                       /* r6: base-priority delta (8-6 = 2) */
            (void*)k_pgThreadNameFmt, /* r7: "%s" name format               */
            1u,                       /* r8: start suspended = 1            */
            0u                        /* r9: processor affinity = 0         */
        );
    }
}
