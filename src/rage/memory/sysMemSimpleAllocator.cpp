/**
 * sysMemSimpleAllocator.cpp — RAGE Simple Memory Allocator vtable methods
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Implements the sysMemSimpleAllocator virtual methods used during boot:
 *   slot  7: SetBreakAllocIndex  @ 0x82186D98
 *   slot  8: Lock               @ 0x82187860
 *   slot  9: Unlock             @ 0x82187870
 *   slot 10: SetLockState       @ 0x82187880
 *   slot 11: IsLocked           @ 0x821878B0
 *   slot 13: TakeSnapshot       @ 0x821878B8
 *   slot 14: DumpLeaks          @ 0x821879B8
 *   slot 15: BeginLogging       @ 0x821878E0
 *   slot 16: EndLogging         @ 0x82187958
 *   slot  5: GetLargestAvailBlock @ 0x82187838
 *   slot  4: GetBucketHead      @ 0x82187840
 *   slot 20: IsAddressOwned     @ 0x82187558
 *   slot  6: Init (ComputeLargestAvail) @ 0x82186DF0
 *
 * Debug string references:
 *   "sysMemSimpleAllocator::Allocate - memory node at %p had guard word trashed!\n"
 *   "sysMemSimpleAllocator::Free - memory at %p already marked free"
 *   "sysMemSimpleAllocator::Free - memory at %p had guard word trashed!\n"
 */

#include <cstdint>
#include <cstddef>
#include <cstring>
#include "../misc/rage_misc.hpp"

/* ── External helpers ─────────────────────────────────────────────────── */

// fiStream::Open — opens a file, returns stream handle (NULL on fail)
// sysMemSimpleAllocator_3650 @ 0x822E3650 (aliased as fiStream_Open)
extern "C" void* fiStream_Open(const char* path, int mode);

// fiStream::Printf — formatted write to open stream
// parStreamOutXml_vprintf @ 0x822E3E40
extern "C" void parStreamOutXml_vprintf(void* stream, const char* format, ...);

// fiStream::Close — closes an open stream
// fiStreamBuf_Close_stub @ 0x822E3B38
extern "C" void fiStreamBuf_Close_stub(void* stream);

// rage_debugLog — debug printf, compiled out (just blr)
extern "C" void rage_debugLog(const char* format, ...);

// Retail diagnostics return without stopping the allocator.
extern "C" void nop_8240E6D0(const char* format, ...);  // @ 0x8240E6D0

/* ── Global: active logging allocator ref count ───────────────────────── */
// lbl_825EBD20 @ 0x825EBD20  (.data, 4 bytes)
extern uint32_t g_activeLoggingAllocatorCount;  // @ 0x825EBD20

namespace rage {

extern "C" void rage_stricmp_6358(uint8_t* buf, uint32_t count);
extern uint32_t g_sysMemAllocationTag;  // @ 0x825EBCE4

// @ 0x82186E40
void* sysMemSimpleAllocator::Allocate(uint32_t size) {
    // Xbox ABI: heads at +0x0C, used bytes at +0x54, tag totals at +0x58,
    // free bytes at +0x98. The scaffold's field names describe these incorrectly.
    uint32_t* words = reinterpret_cast<uint32_t*>(this);
    uint32_t* heads = words + 3;
    struct Node {
        uint32_t guard;
        uint32_t size;
        uint32_t physicalPrev;
        uint32_t flags;
        uint32_t freePrev;
        uint32_t freeNext;
    };
    const auto nodeAt = [](uint32_t address) {
        return reinterpret_cast<Node*>(static_cast<uintptr_t>(address));
    };
    const auto addressOf = [](const Node* node) {
        return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(node));
    };
    const auto bucketFor = [](uint32_t blockSize) {
        // srawi/addze implements signed division, including its truncation to zero.
        int32_t bucket = static_cast<int32_t>(blockSize) / 16;
        return bucket < 15 ? bucket : 15;
    };

    if (isLocked != 0) {
        rage_debugLog("Attempting to allocate %u bytes on a locked heap", size);
    }
    ++allocCount;
    if (allocCount == maxAllocCount) {
        __builtin_trap();
    }
    if (allocCount == 0x04000000) {
        rage_debugLog("Alloc id counter wrapped, may get false hits on leaks.");
        allocCount = 1;
    }

    uint32_t alignedSize = ((size == 0 ? 1 : size) + 15) & ~15u;
    if (alignedSize > largestAvailBlock) {
        rage_debugLog("Not enough memory to allocate %u bytes", alignedSize);
    }

    Node* chosen = nullptr;
    for (int32_t bucket = bucketFor(alignedSize); bucket < 16; ++bucket) {
        uint32_t bestSize = 0xFFFFFFFFu;
        for (Node* node = nodeAt(heads[bucket]); node != nullptr; node = nodeAt(node->freeNext)) {
            if (node->guard != addressOf(node)) {
                rage_debugLog("sysMemSimpleAllocator::Allocate - memory node at %p had guard word trashed!\n\n"
                              "This usually means somebody overran an array between this Allocate call and the\n"
                              "immediately previous Allocate or Free call.", node);
            }
            if (node->size == alignedSize) {
                chosen = node;
                break;
            }
            if (node->size > alignedSize && node->size < bestSize) {
                chosen = node;
                bestSize = node->size;
            }
        }
        if (chosen != nullptr) {
            break;
        }
    }
    if (chosen == nullptr) {
        using LargestFn = uint32_t (*)(sysMemSimpleAllocator*);
        uint32_t largest = reinterpret_cast<LargestFn>(vtable[6])(this);
        rage_debugLog("Not enough memory to allocate %u bytes (fragmented) (largest available block = %u bytes)",
                      alignedSize, largest);
        // Retail next reads null->flags (+0x0C). Keep that fault observable:
        // a plain null dereference is UB and clang would delete this path's tail.
        static_cast<void>(*reinterpret_cast<volatile uint32_t*>(static_cast<uintptr_t>(0x0C)));
    }

    chosen->flags = ((chosen->flags | 0x10u) & 0x3Fu) | (allocCount << 6);
    int32_t bucket = bucketFor(chosen->size);
    uint32_t prev = chosen->freePrev;
    uint32_t next = chosen->freeNext;
    if (prev != 0) {
        nodeAt(prev)->freeNext = next;
    } else {
        heads[bucket] = next;
    }
    if (next != 0) {
        nodeAt(next)->freePrev = prev;
    }

    // A remainder must hold a header and nonempty payload. +16 exactly stays whole.
    if (chosen->size > alignedSize + 16) {
        uint32_t remainderAddress = addressOf(chosen) + alignedSize + 16;
        Node* remainder = nodeAt(remainderAddress);
        remainder->guard = remainderAddress;
        remainder->physicalPrev = addressOf(chosen);
        remainder->flags = 0;
        remainder->size = chosen->size - alignedSize - 16;
        uint32_t following = remainderAddress + remainder->size + 16;
        if (following < heapBase + heapSize && following != 0) {
            nodeAt(following)->physicalPrev = remainderAddress;
        }
        chosen->size = alignedSize;

        bucket = bucketFor(remainder->size);
        remainder->freeNext = heads[bucket];
        if (heads[bucket] != 0) {
            nodeAt(heads[bucket])->freePrev = remainderAddress;
        }
        remainder->freePrev = 0;
        heads[bucket] = remainderAddress;
        largestAvailBlock -= 16;
        words[0x54 / 4] += 16;
    }

    words[0x54 / 4] += chosen->size;
    largestAvailBlock -= chosen->size;
    chosen->flags = (chosen->flags & ~15u) | (g_sysMemAllocationTag & 15u);
    words[0x58 / 4 + (chosen->flags & 15u)] += chosen->size;
    uint8_t* payload = reinterpret_cast<uint8_t*>(chosen) + 16;
    rage_stricmp_6358(payload, chosen->size);
    return payload;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 7: SetBreakAllocIndex  @ 0x82186D98  (8 bytes)
//
// Stores the allocation index at which the allocator should trap.
// When allocCount reaches this value in Allocate(), it triggers
// __builtin_trap() for debugging memory allocation order.
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::SetBreakAllocIndex(uint32_t index) {
    // stw r4,160(r3) — offset 0xA0 = maxAllocCount
    maxAllocCount = index;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 8: Lock  @ 0x82187860  (8 bytes)
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::Lock() {
    // stb 1, 185(r3) — offset 0xB9 = isLocked
    isLocked = 1;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 9: Unlock  @ 0x82187870  (8 bytes)
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::Unlock() {
    // stb 0, 185(r3) — offset 0xB9 = isLocked
    isLocked = 0;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 10: SetLockState  @ 0x82187880  (32 bytes)
//
// Dispatches to Lock() or Unlock() via vtable.
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::SetLockState(bool lock) {
    typedef void (*SlotFn)(sysMemSimpleAllocator*);
    reinterpret_cast<SlotFn>(vtable[lock ? 8 : 9])(this);
}

// ═══════════════════════════════════════════════════════════════════════
// slot 11: IsLocked  @ 0x821878B0  (8 bytes)
// ═══════════════════════════════════════════════════════════════════════
uint8_t sysMemSimpleAllocator::IsLocked() {
    return isLocked;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 5: GetLargestAvailBlock  @ 0x82187838  (8 bytes)
//
// Returns cached largest available block size.
// ═══════════════════════════════════════════════════════════════════════
uint32_t sysMemSimpleAllocator::GetLargestAvailBlock() {
    // lwz r3, 152(r3) — offset 0x98
    return largestAvailBlock;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 4: GetBucketHead  @ 0x82187840  (24 bytes)
//
// Returns the head of the free-list for a given size class (0..15).
// Size classes >= 16 return the overflow list head at +0x54.
// Buckets are stored inline at offsets +0x0C..+0x48 (accessed via
// indexed load: this + (sizeClass + 22) * 4 = this + 0x58 + sizeClass*4
// Wait — let's verify: (sizeClass + 22) * 4 = (sizeClass + 3 + 19)*4
// Actually the scaffold: addi r11,r4,22; rlwinm r10,r11,2,0,29 => (r4+22)*4
// So bucket[i] = *(uint32_t*)((char*)this + (i + 22) * 4)
// i=0: offset 88 (0x58); i=15: offset 148 (0x94)
// ═══════════════════════════════════════════════════════════════════════
void* sysMemSimpleAllocator::GetBucketHead(uint32_t sizeClass) {
    if (sizeClass <= 15) {
        // Buckets stored at this + (sizeClass + 22) * 4
        uint32_t* base = reinterpret_cast<uint32_t*>(this);
        return reinterpret_cast<void*>(base[sizeClass + 22]);
    }
    // Overflow: offset 0x54
    return reinterpret_cast<void*>(overflowHead);
}

// ═══════════════════════════════════════════════════════════════════════
// slot 20: IsAddressOwned  @ 0x82187558  (40 bytes)
//
// Checks if an address falls within [heapBase + 16, heapBase + heapSize).
// The +16 accounts for the heap header/guard at the start.
// ═══════════════════════════════════════════════════════════════════════
bool sysMemSimpleAllocator::IsAddressOwned(void* addr) {
    uintptr_t address = reinterpret_cast<uintptr_t>(addr);
    uintptr_t base = static_cast<uintptr_t>(heapBase);
    uintptr_t start = base + 16;
    uintptr_t end = base + static_cast<uintptr_t>(heapSize);

    if (address < start) {
        return false;
    }
    if (address < end) {
        return true;
    }
    return false;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 13: TakeSnapshot  @ 0x821878B8  (36 bytes)
//
// Records the current allocation count into a snapshot history array.
// The array is stored inline in the object at offsets starting at
// (snapshotIndex + 41) * 4 from 'this'. After recording, increments
// snapshotIndex.
//
// This is used by DumpLeaks to identify allocations that occurred
// after the snapshot was taken.
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::TakeSnapshot() {
    // Store current allocCount at snapshot slot
    // offset = (snapshotIndex + 41) * 4 from this
    uint32_t* base = reinterpret_cast<uint32_t*>(this);
    base[snapshotIndex + 41] = allocCount;

    // Advance snapshot index
    snapshotIndex++;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 14: DumpLeaks  @ 0x821879B8  (300 bytes)
//
// Walks all memory nodes in the heap and reports blocks allocated
// after the most recent snapshot. If a log file path is provided,
// opens it and writes leak details.
//
// Parameters:
//   name    — allocator name (for debug output)
//   logPath — file path to write leak report (NULL = no file output)
//
// Memory node layout (each block has a 16-byte header):
//   +0x00: selfCheck  (should == node address itself)
//   +0x04: blockSize  (size of user data, not including header)
//   +0x0C: flagsMeta  (bit4=allocated flag, bits[6..31]=alloc sequence number)
//   +0x10: prev       (previous node in list)
//   +0x14: next       (next node in list)
//
// The function:
//   1. Pops the last snapshot index to get the allocation count threshold
//   2. Calls Init() (vtable slot 6) to recompute largest available block
//   3. Optionally opens a log file for leak reporting
//   4. Walks all nodes: heapBase -> heapBase + heapSize, stepping by
//      blockSize + 16 (header size)
//   5. For each node with the allocated flag set (bit 4 of flagsMeta)
//      and whose alloc sequence > snapshot threshold, reports a leak
//   6. Closes the log file if opened
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::DumpLeaks(const char* name, const char* logPath) {
    // Pop last snapshot: decrement snapshotIndex, load threshold
    snapshotIndex--;
    uint32_t* base = reinterpret_cast<uint32_t*>(this);
    uint32_t snapshotAllocCount = base[snapshotIndex + 41];

    // Call Init() via vtable (slot 6) to recompute free-list state
    Init();

    // Open log file if path provided
    void* logFile = nullptr;
    if (logPath != nullptr) {
        logFile = fiStream_Open(logPath, 0);
    }

    // Debug output: allocator name
    rage_debugLog("%s", name);

    // Walk all memory nodes in the heap
    uint8_t* heapStart = reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(heapBase));
    uint8_t* heapEnd = heapStart + heapSize;
    uint32_t leakCount = 0;

    uint8_t* node = heapStart;
    while (node != heapEnd) {
        uint32_t flagsMeta = *reinterpret_cast<uint32_t*>(node + 12);

        // Check if allocated (bit 4 set)
        if (flagsMeta & 0x10) {
            // Extract alloc sequence number (bits 6..31)
            uint32_t allocSeq = (flagsMeta >> 6) & 0x3FFFFFF;

            // Only report if allocated after snapshot
            if (allocSeq > snapshotAllocCount) {
                uint32_t blockSize = *reinterpret_cast<uint32_t*>(node + 4);

                // Debug output: block info (nop in retail)
                rage_debugLog("  size:%d tag:%d seq:%d",
                             blockSize, flagsMeta & 0xF, allocSeq);

                // Write to log file if open
                if (logFile != nullptr) {
                    parStreamOutXml_vprintf(logFile, "%d\n",
                                    (flagsMeta >> 6) & 0x3FFFFFF);
                }

                leakCount++;
            }
        }

        // Advance to next node: node += blockSize + 16 (header)
        uint32_t blockSize = *reinterpret_cast<uint32_t*>(node + 4);
        node = node + blockSize + 16;
    }

    // Report total leaks if any found
    if (leakCount > 0) {
        rage_debugLog("  total leaks: %d", leakCount);
    }

    // Close log file if opened
    if (logFile != nullptr) {
        fiStreamBuf_Close_stub(logFile);
    }
}

// ═══════════════════════════════════════════════════════════════════════
// slot 15: BeginLogging  @ 0x821878E0  (116 bytes)
//
// Opens a log file stream for tracking memory allocations.
// The original binary opens files like "c:/logmemory.csv".
// If countRef is true, increments the global active logging counter.
//
// Parameters:
//   path     — file path to open for logging (e.g. "c:/logmemory.csv")
//   countRef — if true, increment global g_activeLoggingAllocatorCount
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::BeginLogging(const char* path, bool countRef) {
    // If countRef requested, increment global counter
    if (countRef) {
        g_activeLoggingAllocatorCount++;
    }

    // Open the log file
    void* stream = fiStream_Open(path, 0);
    logStream = reinterpret_cast<uintptr_t>(stream);

    // Write CSV header if file opened successfully
    if (stream != nullptr) {
        parStreamOutXml_vprintf(stream, "op,address,size,total\n");
    }

    // Store the countRef flag
    isLogging = countRef ? 1 : 0;
}

// ═══════════════════════════════════════════════════════════════════════
// slot 16: EndLogging  @ 0x82187958  (92 bytes)
//
// Closes the log file stream and decrements the global counter
// if BeginLogging was called with countRef=true.
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::EndLogging() {
    // Close log stream if open
    void* stream = reinterpret_cast<void*>(static_cast<uintptr_t>(logStream));
    if (stream != nullptr) {
        fiStreamBuf_Close_stub(stream);
        logStream = 0;
    }

    // Decrement global counter if we were counting refs
    if (isLogging) {
        g_activeLoggingAllocatorCount--;
    }
}

// ═══════════════════════════════════════════════════════════════════════
// slot 6: Init  @ 0x82186DF0  (56 bytes)
//
// Scans all 15 free-list buckets (stored at offsets +0x58..+0x94)
// from highest to lowest to find the first non-empty bucket, then
// walks its chain to find the largest block. Returns the largest
// available block size, also cached in largestAvailBlock.
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::Init() {
    // Scan buckets 14..0 (from +0x48 down to +0x0C in original;
    // in our layout: base[22+14] down to base[22+0])
    uint32_t* base_ptr = reinterpret_cast<uint32_t*>(this);

    // Search from bucket 14 down to 0 for first non-empty
    uint32_t* node = nullptr;
    for (int i = 14; i >= 0; i--) {
        uint32_t bucketHead = base_ptr[i + 22];
        if (bucketHead != 0) {
            node = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(bucketHead));
            break;
        }
    }

    if (node == nullptr) {
        largestAvailBlock = 0;
        return;
    }

    // Walk the free chain to find largest block
    // Node layout: +0x04 = blockSize, +0x14 = next
    uint32_t largest = 0;
    while (node != nullptr) {
        uint32_t blockSize = node[1]; // offset +4
        if (blockSize > largest) {
            largest = blockSize;
        }
        uint32_t next = node[5]; // offset +0x14
        node = (next != 0) ? reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(next)) : nullptr;
    }

    largestAvailBlock = largest;
}

// ═══════════════════════════════════════════════════════════════════════
// Extra at*/sysMem helpers lifted from the 0x82186000 / 0x82187000 /
// 0x8212B000 / 0x82187D00 ranges. These complete the memory-subsystem
// surface used by the boot path: GetSize, destructors, virtual Free
// thunk, spinlock primitive, debug memset, and vfn_19 snapshot hook.
// ═══════════════════════════════════════════════════════════════════════

extern "C" void rage_free_00C0(void* ptr);

// Guarded-init lock shared across rage singletons (process-wide).
// @ 0x825EBCF8  [.data]
extern uint32_t g_sysMemAllocatorInitLock;  // @ 0x825EBCF8

// Debug fill flag for rage_stricmp_6358 (actually a memset-variant).
// @ 0x8260642D  [.data]
extern "C" uint8_t g_sysMemDebugFillFlag;  // @ 0x8260642D

// Forward declaration — defined below.
extern "C" void sysMemSimpleAllocator_SpinAcquire(uint32_t* lock);

// ═══════════════════════════════════════════════════════════════════════
// sysMemSimpleAllocator::GetSize  @ 0x821874D8  (124 bytes)
//
// Returns the block size of a pointer previously returned by Allocate,
// or 0 if the pointer is outside [heapBase, heapBase+heapSize) or not
// allocated. Validates selfCheck (header[+0x00] must equal header addr)
// and the allocated flag (bit 4 of flagsMeta @ +0x0C).
// ═══════════════════════════════════════════════════════════════════════
uint32_t sysMemSimpleAllocator_GetSize_impl(sysMemSimpleAllocator* self, void* ptr) {
    uint32_t addr = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(ptr));

    if (addr < self->heapBase) {
        return 0;
    }
    if (addr >= self->heapBase + self->heapSize) {
        return 0;
    }

    uint32_t* header = reinterpret_cast<uint32_t*>(
        static_cast<uintptr_t>(addr - 16));

    uint32_t flagsMeta = header[3];           // +0x0C
    if ((flagsMeta & 0x10) == 0) {
        // Not allocated (nop_8240E6D0 in retail — compiled out)
        return 0;
    }
    if (header[0] != reinterpret_cast<uintptr_t>(header)) {
        // selfCheck trashed
        return 0;
    }
    return header[1];                          // blockSize @ +0x04
}

// ═══════════════════════════════════════════════════════════════════════
// sysMemSimpleAllocator::~sysMemSimpleAllocator (vfn_0) @ 0x82186C58
//
// Retail destructor — most cleanup compiled out; just falls through to
// the shared epilogue (decrement init-lock handled by ScalarDtor).
// ═══════════════════════════════════════════════════════════════════════
sysMemSimpleAllocator::~sysMemSimpleAllocator() {
    // No heap teardown in retail: allocator owns a fixed heap region
    // reclaimed by the OS on shutdown.
}

// ═══════════════════════════════════════════════════════════════════════
// sysMemSimpleAllocator::ScalarDtor (vfn_1) @ 0x82186DA0  (76 bytes)
//
// MSVC scalar deleting destructor thunk. Acquires init-lock, dispatches
// to the non-virtual Allocate (the scaffold calls 0x82186E40 which is
// the allocator body — this is the delete-on-behalf-of-derived variant
// where r5 carries the flags), releases the lock.
//
// In the retail scaffold this tail-calls the allocator body to finalize
// pending frees scheduled during destruction; we preserve that call.
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::ScalarDtor(int flags) {
    sysMemSimpleAllocator_SpinAcquire(&g_sysMemAllocatorInitLock);

    // Retail dispatches through Allocate's finalize path — emulate as
    // running the destructor body (no-op in retail) + optional free.
    this->~sysMemSimpleAllocator();
    if (flags & 1) {
        rage_free_00C0(this);
    }

    __sync_synchronize();  // lwsync
    g_sysMemAllocatorInitLock = 0;
}

// Non-virtual Free body (788 bytes); the locking thunk follows below.
// @ 0x821871C0
extern "C" void sysMemSimpleAllocator_Free_body(sysMemSimpleAllocator* self, void* ptr) {
    // Keep the Xbox's 32-bit links. The shared struct currently misnames these
    // fields: +0x0C..+0x48 are heads, +0x54 is allocated bytes, +0x58..+0x94
    // are tag totals, and +0x98 is total free bytes (not the largest block).
    uint32_t* heap = reinterpret_cast<uint32_t*>(self);
    struct Node {
        uint32_t guard;
        uint32_t size;
        uint32_t physicalPrev;
        uint32_t flags;
        uint32_t freePrev;
        uint32_t freeNext;
    };
    auto nodeAt = [](uint32_t address) {
        return reinterpret_cast<Node*>(static_cast<uintptr_t>(address));
    };
    auto sizeClass = [](uint32_t size) {
        // srawi/addze: signed division rounds toward zero, then caps at 15.
        int32_t index = static_cast<int32_t>(size) / 16;
        return index < 15 ? index : 15;
    };
    auto unlink = [&](Node* node) {
        int32_t index = sizeClass(node->size);
        if (node->freePrev != 0) {
            nodeAt(node->freePrev)->freeNext = node->freeNext;
        } else {
            heap[index + 3] = node->freeNext;
        }
        if (node->freeNext != 0) {
            nodeAt(node->freeNext)->freePrev = node->freePrev;
        }
    };

    if (self->isLocked != 0) {
        nop_8240E6D0("Attempting to free memory from a locked heap (%p)");
    }
    using IsOwned = uint32_t (*)(sysMemSimpleAllocator*, void*);
    if (static_cast<uint8_t>(reinterpret_cast<IsOwned>(self->vtable[20])(self, ptr)) == 0) {
        nop_8240E6D0("Attempting to free memory not allocated from this heap");
    }

    uint32_t address = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(ptr)) - 16;
    Node* node = nodeAt(address);
    if ((node->flags & 0x10) == 0) {
        nop_8240E6D0("sysMemSimpleAllocator::Free - memory at %p already marked free", ptr);
    }
    node->flags &= ~0x10u;
    if (node->guard != address) {
        nop_8240E6D0("sysMemSimpleAllocator::Free - memory at %p had guard word trashed!\n\n"
                    "This usually means somebody overran an array between this Free call\n"
                    "and the immediately previous Allocate or Free call.", ptr);
    }

    // Retail's poison fill stops 16 bytes before the payload end.
    std::memset(ptr, 0xDD, node->size - 16);
    heap[0x98 / 4] += node->size;
    heap[0x54 / 4] -= node->size;
    heap[0x58 / 4 + (node->flags & 0xF)] -= node->size;

    uint32_t end = heap[0x04 / 4] + heap[0x4C / 4];
    uint32_t nextAddress = address + node->size + 16;
    if (nextAddress != 0 && nextAddress < end) {
        Node* next = nodeAt(nextAddress);
        if ((next->flags & 0x10) == 0) {
            node->size += next->size + 16;
            heap[0x98 / 4] += 16;
            heap[0x54 / 4] -= 16;
            unlink(next);

            uint32_t afterNext = nextAddress + next->size + 16;
            end = heap[0x04 / 4] + heap[0x4C / 4];
            if (afterNext != 0 && afterNext < end) {
                nodeAt(afterNext)->physicalPrev = address;
            }
        }
    }

    if (node->physicalPrev != 0) {
        Node* prev = nodeAt(node->physicalPrev);
        if ((prev->flags & 0x10) == 0) {
            unlink(prev);
            prev->size += node->size + 16;
            heap[0x98 / 4] += 16;
            heap[0x54 / 4] -= 16;

            end = heap[0x04 / 4] + heap[0x4C / 4];
            nextAddress = address + node->size + 16;
            if (nextAddress != 0 && nextAddress < end) {
                nodeAt(nextAddress)->physicalPrev = node->physicalPrev;
            }
            address = node->physicalPrev;
            node = prev;
        }
    }

    int32_t index = sizeClass(node->size);
    node->freeNext = heap[index + 3];
    if (heap[index + 3] != 0) {
        nodeAt(heap[index + 3])->freePrev = address;
    }
    node->freePrev = 0;
    heap[index + 3] = address;
}

// ═══════════════════════════════════════════════════════════════════════
// sysMemSimpleAllocator::Free (vfn_2) @ 0x82187178  (68 bytes)
//
// Virtual Free thunk. Acquires init-lock, delegates to the non-virtual
// Free body at 0x821871C0, releases lock.
// ═══════════════════════════════════════════════════════════════════════
void sysMemSimpleAllocator::Free(void* ptr) {
    sysMemSimpleAllocator_SpinAcquire(&g_sysMemAllocatorInitLock);
    sysMemSimpleAllocator_Free_body(this, ptr);
    __sync_synchronize();
    g_sysMemAllocatorInitLock = 0;
}

// ═══════════════════════════════════════════════════════════════════════
// sysMemSimpleAllocator_SpinAcquire  @ 0x82187D90  (184 bytes)
//
// MSVC guarded-init spinlock with exponential backoff. CAS 0->1, else
// busy-wait `delay` iterations (starting at 8, doubling up to 16384),
// then retry. Values other than 0 or 1 return unchanged. The original uses
// lwarx/stwcx + MSR guards; we use host
// atomics which provide equivalent ordering.
// ═══════════════════════════════════════════════════════════════════════
extern "C" void sysMemSimpleAllocator_SpinAcquire(uint32_t* lock) {
    uint32_t delay = 8;
    for (;;) {
        uint32_t previous = __sync_val_compare_and_swap(lock, 0u, 1u);
        if (previous != 1) {
            __sync_synchronize();  // lwsync after acquire
            return;
        }
        // Busy-wait `delay` iterations
        for (volatile uint32_t i = 0; i < delay; ++i) {
            // empty
        }
        if (delay < 16384) {
            delay <<= 1;
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// rage_stricmp_6358  @ 0x821862A0  (180 bytes)
// (Symbol prefix "sysMemSimpleAllocator_62A0_p46" is the pass5 alias.)
//
// Debug memset variant. Dispatches on global flag:
//   - g_sysMemDebugFillFlag != 0 : fill each byte with its address low byte
//   - otherwise                  : fill with 0xCDCDCDCD ("heap garbage"
//                                  pattern), 4 bytes at a time, per-byte
//                                  tail.
// Parameters: (buf, count)
// ═══════════════════════════════════════════════════════════════════════
extern "C" void rage_stricmp_6358(uint8_t* buf, uint32_t count) {
    if (g_sysMemDebugFillFlag != 0) {
        for (uint32_t i = 0; i < count; ++i) {
            buf[i] = static_cast<uint8_t>(reinterpret_cast<uintptr_t>(buf + i));
        }
        return;
    }

    constexpr uint32_t kDebugPattern = 0xCDCDCDCDu;
    uint32_t remaining = count;
    uint8_t* cur = buf;

    if (remaining > 3) {
        uint32_t words = ((remaining - 4) >> 2) + 1;
        for (uint32_t i = 0; i < words; ++i) {
            *reinterpret_cast<uint32_t*>(cur) = kDebugPattern;
            cur += 4;
            remaining -= 4;
        }
    }

    uint32_t pattern = kDebugPattern;
    while (remaining != 0) {
        *cur++ = static_cast<uint8_t>(pattern);
        pattern = (pattern >> 8) | (pattern << 24);
        --remaining;
    }
}

// ═══════════════════════════════════════════════════════════════════════
// sysMemSimpleAllocator::vfn_19  @ 0x82187588  (84 bytes)
//
// Acquires init-lock, invokes the atSingleton tail handler at 0x821875E0
// (a snapshot/commit hook for this allocator), releases lock.
// ═══════════════════════════════════════════════════════════════════════
extern "C" void atSingleton_75E0_fw(sysMemSimpleAllocator* self);

void sysMemSimpleAllocator_vfn_19_impl(sysMemSimpleAllocator* self) {
    sysMemSimpleAllocator_SpinAcquire(&g_sysMemAllocatorInitLock);
    atSingleton_75E0_fw(self);
    __sync_synchronize();
    g_sysMemAllocatorInitLock = 0;
}

// ═══════════════════════════════════════════════════════════════════════
// sysMemAllocator::~sysMemAllocator (vfn_0) @ 0x8212B098  (72 bytes)
//
// Base-class scalar-deleting destructor for rage::sysMemAllocator.
// Re-plants the base vtable (from lbl @ 0x820332C4 region) and frees
// the object if flags & 1.
// ═══════════════════════════════════════════════════════════════════════
extern "C" void** g_sysMemAllocator_vtable;  // @ 0x820332C4

void sysMemAllocator_ScalarDtor_impl(sysMemAllocator* self, int flags) {
    self->vtable = g_sysMemAllocator_vtable;
    if (flags & 1) {
        rage_free_00C0(self);
    }
}

// ── TODO notes ─────────────────────────────────────────────────────────
// TODO(sysMem): replace the hand-rolled SpinAcquire with the real
//   rage::sysIpcCriticalSection primitive once rage IPC is lifted.
// TODO(sysMem): g_sysMemAllocatorInitLock (0x825EBCF8) is a process-wide
//   guarded-init lock shared by many rage singletons — move to a
//   dedicated guarded_init header when more users are lifted.
// TODO(sysMem): verify exact vtable slot for GetSize (alias 12 vs 20)
//   once the full sysMemSimpleAllocator vtable is reconstructed.
// TODO(sysMem): rage_stricmp_6358 name is a recomp-pass artifact; real
//   symbol is a debug memset (rage_debugHeapFill). Rename in a later
//   global rename pass.

} // namespace rage
