/* Platform-independent Xbox kernel services. */
#include "xam/kernel.h"
#include <stdlib.h>
#include <string.h>
#include <signal.h>

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

/**
 * DbgBreakPoint @ 0x8258662C
 *
 * Triggers a breakpoint for debugging.
 */
void DbgBreakPoint(void) {
#ifdef _WIN32
    __builtin_trap();
#elif defined(__GNUC__) || defined(__clang__)
    __builtin_trap();
#else
    // Fallback: raise SIGTRAP
    raise(SIGTRAP);
#endif
}

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
