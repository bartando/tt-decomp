/**
 * Xbox 360 Kernel API Implementation - Cross-Platform
 * Rockstar Presents Table Tennis
 * 
 * Implements Xbox 360 kernel functions using POSIX threads and standard C library.
 * Provides TLS, synchronization primitives, and memory management.
 */

#include "xam/kernel.h"
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <signal.h>

#ifdef __APPLE__
#include <mach/mach_time.h>
#endif

//=============================================================================
// Thread-Local Storage Implementation
//=============================================================================

#define MAX_TLS_SLOTS 64

static struct {
    pthread_key_t key;
    uint8_t allocated;
} g_tls_slots[MAX_TLS_SLOTS] = {0};

static pthread_mutex_t g_tls_mutex = PTHREAD_MUTEX_INITIALIZER;

/**
 * KeTlsAlloc @ 0x8258623C
 */
uint32_t KeTlsAlloc(void) {
    pthread_mutex_lock(&g_tls_mutex);
    
    for (uint32_t i = 0; i < MAX_TLS_SLOTS; i++) {
        if (!g_tls_slots[i].allocated) {
            if (pthread_key_create(&g_tls_slots[i].key, NULL) == 0) {
                g_tls_slots[i].allocated = 1;
                pthread_mutex_unlock(&g_tls_mutex);
                return i;
            }
        }
    }
    
    pthread_mutex_unlock(&g_tls_mutex);
    return 0xFFFFFFFF;  // No slots available
}

/**
 * KeTlsFree @ 0x8258624C
 */
uint32_t KeTlsFree(uint32_t dwTlsIndex) {
    if (dwTlsIndex >= MAX_TLS_SLOTS) {
        return 0;
    }
    
    pthread_mutex_lock(&g_tls_mutex);
    
    if (g_tls_slots[dwTlsIndex].allocated) {
        pthread_key_delete(g_tls_slots[dwTlsIndex].key);
        g_tls_slots[dwTlsIndex].allocated = 0;
        pthread_mutex_unlock(&g_tls_mutex);
        return 1;
    }
    
    pthread_mutex_unlock(&g_tls_mutex);
    return 0;
}

/**
 * KeTlsGetValue @ 0x8258621C
 */
void* KeTlsGetValue(uint32_t dwTlsIndex) {
    if (dwTlsIndex >= MAX_TLS_SLOTS) return NULL;
    pthread_mutex_lock(&g_tls_mutex);
    void* value = g_tls_slots[dwTlsIndex].allocated ? pthread_getspecific(g_tls_slots[dwTlsIndex].key) : NULL;
    pthread_mutex_unlock(&g_tls_mutex);
    return value;
}

/**
 * KeTlsSetValue @ 0x8258622C
 */
uint32_t KeTlsSetValue(uint32_t dwTlsIndex, void* lpTlsValue) {
    if (dwTlsIndex >= MAX_TLS_SLOTS) return 0;
    pthread_mutex_lock(&g_tls_mutex);
    uint32_t result = g_tls_slots[dwTlsIndex].allocated && pthread_setspecific(g_tls_slots[dwTlsIndex].key, lpTlsValue) == 0;
    pthread_mutex_unlock(&g_tls_mutex);
    return result;
}

// Synchronization lives in platform/host_sync.cpp.

//=============================================================================
// Critical Region Implementation
//=============================================================================

// Critical regions on Xbox 360 disable kernel APCs
// For cross-platform, we use a simple counter per thread
static __thread int32_t g_critical_region_count = 0;

/**
 * KeEnterCriticalRegion @ 0x825864AC
 */
void KeEnterCriticalRegion(void) {
    g_critical_region_count++;
}

/**
 * KeLeaveCriticalRegion @ 0x8258649C
 */
void KeLeaveCriticalRegion(void) {
    if (g_critical_region_count > 0) {
        g_critical_region_count--;
    }
}

//=============================================================================
// Memory Management Implementation (XAM)
//=============================================================================

/**
 * XamAlloc @ 0x8258676C
 */
void* XamAlloc(uint32_t dwFlags, uint32_t dwSize) {
    (void)dwFlags;
    
    if (dwSize == 0) {
        return NULL;
    }
    
    void* ptr = malloc(dwSize);
    if (ptr) {
        memset(ptr, 0, dwSize);  // XamAlloc zero-initializes
    }
    
    return ptr;
}

/**
 * XamFree @ 0x8258675C
 */
void XamFree(void* pAddress) {
    if (pAddress) {
        free(pAddress);
    }
}

//=============================================================================
// Performance Counter Implementation
//=============================================================================

/**
 * KeQueryPerformanceFrequency @ 0x825865EC
 */
uint64_t KeQueryPerformanceFrequency(void) {
#ifdef __APPLE__
    // macOS: Use mach_timebase_info
    static mach_timebase_info_data_t timebase = {0};
    if (timebase.denom == 0) {
        mach_timebase_info(&timebase);
    }
    // Convert to Hz (nanoseconds to seconds)
    return 1000000000ULL * timebase.denom / timebase.numer;
#else
    // Linux/Windows: Assume nanosecond precision
    return 1000000000ULL;  // 1 GHz
#endif
}

//=============================================================================
// Yield/Sleep Implementation
//=============================================================================

/**
 * NtYieldExecution @ 0x8258659C
 */
NTSTATUS NtYieldExecution(void) {
    // Yield to other threads
    #ifdef _WIN32
        SwitchToThread();
    #else
        sched_yield();
    #endif
    
    return STATUS_SUCCESS;
}

// Aligned allocations and size tracking live in platform/host_memory.cpp.

/**
 * MmQueryStatistics @ 0x825865FC
 * 
 * Queries system memory statistics.
 */
NTSTATUS MmQueryStatistics(MM_STATISTICS* pStatistics) {
    if (!pStatistics) {
        return STATUS_INVALID_PARAMETER;
    }
    
    // Return fake statistics
    memset(pStatistics, 0, sizeof(MM_STATISTICS));
    
    // Fake values (Xbox 360 has 512MB RAM)
    pStatistics->TotalPhysicalPages = 131072;  // 512MB / 4KB pages
    pStatistics->AvailablePages = 65536;       // 256MB available
    pStatistics->CachedPages = 16384;          // 64MB cached
    pStatistics->PoolPages = 8192;             // 32MB pool
    
    return STATUS_SUCCESS;
}

/**
 * MmQueryAddressProtect @ 0x825862AC
 * 
 * Queries the protection flags for a memory address.
 */
uint32_t MmQueryAddressProtect(void* pAddress) {
    (void)pAddress;
    
    // Return read/write/execute (typical for game memory)
    return 0x00000007;  // PAGE_EXECUTE_READWRITE
}

//=============================================================================
// Debug Functions Implementation
//=============================================================================

/**
 * DbgBreakPoint @ 0x8258662C
 * 
 * Triggers a breakpoint for debugging.
 */
void DbgBreakPoint(void) {
#ifdef _WIN32
    __debugbreak();
#elif defined(__GNUC__) || defined(__clang__)
    __builtin_trap();
#else
    // Fallback: raise SIGTRAP
    raise(SIGTRAP);
#endif
}

//=============================================================================
// String Functions Implementation
//=============================================================================

/**
 * RtlInitAnsiString @ 0x8258664C
 * 
 * Initializes an ANSI_STRING structure.
 */
void RtlInitAnsiString(ANSI_STRING* DestinationString, const char* SourceString) {
    if (!DestinationString) {
        return;
    }
    
    if (SourceString == NULL) {
        DestinationString->Length = 0;
        DestinationString->MaximumLength = 0;
        DestinationString->Buffer = NULL;
    } else {
        size_t length = strlen(SourceString);
        
        // Clamp to UINT16_MAX
        if (length > 0xFFFE) {
            length = 0xFFFE;
        }
        
        DestinationString->Length = (uint16_t)length;
        DestinationString->MaximumLength = (uint16_t)(length + 1);  // Include null terminator
        DestinationString->Buffer = (char*)SourceString;
    }
}

//=============================================================================
// Error Code Conversion Implementation
//=============================================================================

/**
 * RtlNtStatusToDosError @ 0x82585E5C
 * 
 * Converts NTSTATUS to Win32 error code.
 */
uint32_t RtlNtStatusToDosError(NTSTATUS Status) {
    // Common NTSTATUS to Win32 error mappings
    switch (Status) {
        case STATUS_SUCCESS:
            return ERROR_SUCCESS;
        
        case STATUS_TIMEOUT:
            return 0x000005B4;  // ERROR_TIMEOUT
        
        case STATUS_SEMAPHORE_LIMIT_EXCEEDED:
            return 298; // ERROR_TOO_MANY_POSTS

        case STATUS_PENDING:
            return 0x000003E5;  // ERROR_IO_PENDING
        
        case STATUS_NO_MEMORY:
            return 0x00000008;  // ERROR_NOT_ENOUGH_MEMORY
        
        case STATUS_INVALID_PARAMETER:
            return 0x00000057;  // ERROR_INVALID_PARAMETER
        
        case 0xC0000001:  // STATUS_UNSUCCESSFUL
            return 0x0000001F;  // ERROR_GEN_FAILURE
        
        case 0xC0000002:  // STATUS_NOT_IMPLEMENTED
            return 0x00000078;  // ERROR_CALL_NOT_IMPLEMENTED
        
        case 0xC0000008:  // STATUS_INVALID_HANDLE
            return 0x00000006;  // ERROR_INVALID_HANDLE
        
        case 0xC000000F:  // STATUS_NO_SUCH_FILE
            return 0x00000002;  // ERROR_FILE_NOT_FOUND
        
        case 0xC0000010:  // STATUS_INVALID_DEVICE_REQUEST
            return 0x00000001;  // ERROR_INVALID_FUNCTION
        
        case 0xC0000022:  // STATUS_ACCESS_DENIED
            return 0x00000005;  // ERROR_ACCESS_DENIED
        
        case 0xC0000034:  // STATUS_OBJECT_NAME_NOT_FOUND
            return 0x00000002;  // ERROR_FILE_NOT_FOUND
        
        case 0xC0000035:  // STATUS_OBJECT_NAME_COLLISION
            return 0x000000B7;  // ERROR_ALREADY_EXISTS
        
        case 0xC000009A:  // STATUS_INSUFFICIENT_RESOURCES
            return 0x00000008;  // ERROR_NOT_ENOUGH_MEMORY
        
        case 0xC00000BB:  // STATUS_NOT_SUPPORTED
            return 0x00000032;  // ERROR_NOT_SUPPORTED
        
        default:
            // For unknown status codes, return generic failure
            return 0x0000001F;  // ERROR_GEN_FAILURE
    }
}

//=============================================================================
// XEX Header Functions Implementation
//=============================================================================

/**
 * RtlImageXexHeaderField @ 0x82585E3C
 * 
 * Retrieves a field from the XEX header.
 * 
 * Note: This is a stub implementation for cross-platform compatibility.
 * On Xbox 360, this would parse the actual XEX header structure.
 */
void* RtlImageXexHeaderField(void* XexHeaderBase, uint32_t ImageField) {
    (void)XexHeaderBase;
    (void)ImageField;
    
    // Stub: Return NULL for all fields
    // In a full implementation, this would parse the XEX header structure
    // and return pointers to the requested field data
    
    return NULL;
}

//=============================================================================
// Physical Memory Functions Implementation
//=============================================================================

/**
 * MmGetPhysicalAddress @ 0x8258630C
 * 
 * Converts virtual address to physical address.
 * 
 * On Xbox 360, memory is directly mapped, so virtual == physical for most addresses.
 * For cross-platform, we just return the virtual address as a 64-bit value.
 */
uint64_t MmGetPhysicalAddress(void* BaseAddress) {
    // On Xbox 360, virtual addresses are directly mapped to physical
    // For cross-platform, return the virtual address
    return (uint64_t)(uintptr_t)BaseAddress;
}

// Synchronization lives in platform/host_sync.cpp.

//=============================================================================
// Spinlock Implementation
//=============================================================================

// Spinlock implementation using atomic operations
// On Xbox 360, spinlocks are used for very short critical sections at raised IRQL

#ifdef _WIN32
#include <windows.h>
#define SPINLOCK_INIT 0
#define spinlock_lock(lock) while (InterlockedCompareExchange((volatile LONG*)(lock), 1, 0) != 0) { _mm_pause(); }
#define spinlock_unlock(lock) InterlockedExchange((volatile LONG*)(lock), 0)
#define spinlock_trylock(lock) (InterlockedCompareExchange((volatile LONG*)(lock), 1, 0) == 0)
#else
#include <stdatomic.h>
#define SPINLOCK_INIT 0
#if defined(__x86_64__) || defined(__i386__)
#define spinlock_lock(lock) while (atomic_exchange_explicit((_Atomic uint32_t*)(lock), 1, memory_order_acquire) != 0) { __asm__ __volatile__("pause" ::: "memory"); }
#elif defined(__aarch64__)
#define spinlock_lock(lock) while (atomic_exchange_explicit((_Atomic uint32_t*)(lock), 1, memory_order_acquire) != 0) { __asm__ __volatile__("yield" ::: "memory"); }
#else
#define spinlock_lock(lock) while (atomic_exchange_explicit((_Atomic uint32_t*)(lock), 1, memory_order_acquire) != 0) { /* spin */ }
#endif
#define spinlock_unlock(lock) atomic_store_explicit((_Atomic uint32_t*)(lock), 0, memory_order_release)
#define spinlock_trylock(lock) (atomic_exchange_explicit((_Atomic uint32_t*)(lock), 1, memory_order_acquire) == 0)
#endif

// Thread-local IRQL level (simplified)
static __thread uint32_t g_current_irql = 0;

/**
 * KeRaiseIrqlToDpcLevel @ 0x820007ec
 * 
 * Raises IRQL to DISPATCH_LEVEL.
 */
uint32_t KeRaiseIrqlToDpcLevel(void) {
    uint32_t old_irql = g_current_irql;
    g_current_irql = 2;  // DISPATCH_LEVEL
    return old_irql;
}

/**
 * KeAcquireSpinLockAtRaisedIrql @ 0x82000760
 * 
 * Acquires a spinlock at raised IRQL.
 */
void KeAcquireSpinLockAtRaisedIrql(KSPIN_LOCK* SpinLock) {
    if (!SpinLock) {
        return;
    }
    
    spinlock_lock(SpinLock);
}

/**
 * KeReleaseSpinLockFromRaisedIrql @ 0x82000754
 * 
 * Releases a spinlock at raised IRQL.
 */
void KeReleaseSpinLockFromRaisedIrql(KSPIN_LOCK* SpinLock) {
    if (!SpinLock) {
        return;
    }
    
    spinlock_unlock(SpinLock);
}

/**
 * KeTryToAcquireSpinLockAtRaisedIrql @ 0x82000800
 * 
 * Attempts to acquire a spinlock without blocking.
 */
uint32_t KeTryToAcquireSpinLockAtRaisedIrql(KSPIN_LOCK* SpinLock) {
    if (!SpinLock) {
        return 0;
    }
    
    return spinlock_trylock(SpinLock) ? 1 : 0;
}

//=============================================================================
// L2 Cache Lock Implementation
//=============================================================================

/**
 * KeLockL2 @ 0x820007e0
 * 
 * Locks the L2 cache (Xbox 360 specific).
 * Cross-platform: No-op (modern CPUs handle cache coherency automatically).
 */
void KeLockL2(void) {
    // No-op on modern systems
    // Xbox 360 has explicit L2 cache locking for DMA operations
}

/**
 * KeUnlockL2 @ 0x820007e4
 * 
 * Unlocks the L2 cache.
 */
void KeUnlockL2(void) {
    // No-op on modern systems
}

//=============================================================================
// System Time Implementation
//=============================================================================

/**
 * KeQuerySystemTime @ 0x82000850
 * 
 * Queries the current system time.
 * Returns time as 100-nanosecond intervals since January 1, 1601 (Windows FILETIME).
 */
void KeQuerySystemTime(LARGE_INTEGER* CurrentTime) {
    if (!CurrentTime) {
        return;
    }
    
#ifdef _WIN32
    // Windows: Use GetSystemTimeAsFileTime
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    *CurrentTime = ((int64_t)ft.dwHighDateTime << 32) | ft.dwLowDateTime;
#else
    // POSIX: Convert from Unix epoch (1970) to Windows epoch (1601)
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    
    // Unix epoch (1970-01-01) is 11644473600 seconds after Windows epoch (1601-01-01)
    const int64_t UNIX_EPOCH_OFFSET = 116444736000000000LL;
    
    // Convert to 100-nanosecond intervals
    int64_t time_100ns = (int64_t)ts.tv_sec * 10000000LL + ts.tv_nsec / 100;
    *CurrentTime = time_100ns + UNIX_EPOCH_OFFSET;
#endif
}

//=============================================================================
// Thread Delay Implementation
//=============================================================================

/**
 * KeDelayExecutionThread @ 0x82000874
 * 
 * Delays execution of the current thread.
 */
NTSTATUS KeDelayExecutionThread(uint32_t WaitMode, uint32_t Alertable, LARGE_INTEGER* Interval) {
    (void)WaitMode;
    (void)Alertable;
    
    if (!Interval) {
        return STATUS_INVALID_PARAMETER;
    }
    
    // Interval is in 100-nanosecond units
    // Negative = relative time, Positive = absolute time
    int64_t delay_100ns = *Interval;
    
    if (delay_100ns >= 0) {
        // Absolute time - not commonly used, treat as relative
        // In a full implementation, we'd calculate time until target
        return STATUS_SUCCESS;
    }
    
    // Relative time (negative value)
    delay_100ns = -delay_100ns;
    
    // Convert to nanoseconds
    int64_t delay_ns = delay_100ns * 100;
    
    // Sleep
#ifdef _WIN32
    // Windows: Use Sleep (milliseconds)
    DWORD delay_ms = (DWORD)(delay_ns / 1000000);
    if (delay_ms == 0 && delay_ns > 0) {
        delay_ms = 1;  // Minimum 1ms
    }
    Sleep(delay_ms);
#else
    // POSIX: Use nanosleep
    struct timespec ts;
    ts.tv_sec = delay_ns / 1000000000LL;
    ts.tv_nsec = delay_ns % 1000000000LL;
    nanosleep(&ts, NULL);
#endif
    
    return STATUS_SUCCESS;
}

//=============================================================================
// Thread Management Implementation
//=============================================================================

// Thread start wrapper structure
typedef struct {
    void* (*start_routine)(void*);
    void* parameter;
} ThreadStartInfo;

// Thread start wrapper function
static void* thread_start_wrapper(void* arg) {
    ThreadStartInfo* info = (ThreadStartInfo*)arg;
    void* (*start_routine)(void*) = info->start_routine;
    void* parameter = info->parameter;
    free(info);
    
    return start_routine(parameter);
}

/**
 * ExCreateThread @ 0x820007dc
 * 
 * Creates a new thread.
 */
NTSTATUS ExCreateThread(HANDLE* ThreadHandle, uint32_t StackSize, uint32_t* ThreadId,
                        void* StartAddress, void* Parameter, uint32_t CreationFlags) {
    (void)StackSize;  // pthread doesn't easily support custom stack size
    (void)CreationFlags;  // Simplified: always start immediately
    
    if (!ThreadHandle || !StartAddress) {
        return STATUS_INVALID_PARAMETER;
    }
    
    // Allocate thread start info
    ThreadStartInfo* info = (ThreadStartInfo*)malloc(sizeof(ThreadStartInfo));
    if (!info) {
        return STATUS_NO_MEMORY;
    }
    
    info->start_routine = (void* (*)(void*))StartAddress;
    info->parameter = Parameter;
    
    // Create thread
    pthread_t* thread = (pthread_t*)malloc(sizeof(pthread_t));
    if (!thread) {
        free(info);
        return STATUS_NO_MEMORY;
    }
    
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
    
    int result = pthread_create(thread, &attr, thread_start_wrapper, info);
    pthread_attr_destroy(&attr);
    
    if (result != 0) {
        free(thread);
        free(info);
        return STATUS_NO_MEMORY;
    }
    
    *ThreadHandle = (HANDLE)thread;
    
    if (ThreadId) {
        // pthread_t is not directly convertible to uint32_t on all platforms
        // Use a hash or just cast (simplified)
        *ThreadId = (uint32_t)(uintptr_t)thread;
    }
    
    return STATUS_SUCCESS;
}

/**
 * ExTerminateThread @ 0x82000840
 * 
 * Terminates a thread.
 */
NTSTATUS ExTerminateThread(HANDLE ThreadHandle, NTSTATUS ExitStatus) {
    (void)ExitStatus;
    
    if (!ThreadHandle) {
        return STATUS_INVALID_PARAMETER;
    }
    
    pthread_t* thread = (pthread_t*)ThreadHandle;
    
    // Cancel the thread
    pthread_cancel(*thread);
    
    // Wait for it to terminate
    pthread_join(*thread, NULL);
    
    // Free the handle
    free(thread);
    
    return STATUS_SUCCESS;
}

//=============================================================================
// Exception Handling Functions Implementation
//=============================================================================

/**
 * RtlCaptureContext @ 0x8258628C
 * 
 * Captures the current CPU context.
 * 
 * Note: This is a simplified stub implementation.
 * Full implementation would capture all CPU registers.
 */
void RtlCaptureContext(CONTEXT* ContextRecord) {
    if (!ContextRecord) {
        return;
    }
    
    // Zero out the context
    memset(ContextRecord, 0, sizeof(CONTEXT));
    
    // Set context flags to indicate what's valid
    ContextRecord->ContextFlags = 0x00000001;  // CONTEXT_CONTROL
    
    // On x86/x64, we could use inline assembly or compiler intrinsics
    // For cross-platform, we provide a minimal stub
    
#if defined(__GNUC__) || defined(__clang__)
    // Capture program counter (return address)
    ContextRecord->Pc = (uint32_t)(uintptr_t)__builtin_return_address(0);
    
    // Capture frame pointer
    ContextRecord->Gpr[1] = (uint32_t)(uintptr_t)__builtin_frame_address(0);
#endif
}

/**
 * RtlUnwind @ 0x8258629C
 * 
 * Unwinds the stack for exception handling.
 * 
 * Note: This is a stub implementation for cross-platform compatibility.
 * Full implementation would walk the stack and call exception handlers.
 */
void RtlUnwind(void* TargetFrame, void* TargetIp, void* ExceptionRecord, void* ReturnValue) {
    (void)TargetFrame;
    (void)TargetIp;
    (void)ExceptionRecord;
    (void)ReturnValue;
    
    // Stub: In a full implementation, this would:
    // 1. Walk the stack from current frame to TargetFrame
    // 2. Call exception handlers for each frame
    // 3. Restore context to TargetFrame
    // 4. Jump to TargetIp with ReturnValue
    
    // For cross-platform, we rely on C++ exceptions instead
}

// Host threads have no hardware IRQL; retain the per-thread nesting value.
void KfLowerIrql(uint32_t irql) { g_current_irql = irql; }
