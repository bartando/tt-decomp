#include "xam/kernel.h"
#include "xam/thread_sync.h"
#include "platform/host_error.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition) do { if (!(condition)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #condition); exit(1); \
} } while (0)

typedef struct {
    RTL_CRITICAL_SECTION* lock;
    HANDLE event;
    uint32_t tls;
    int value;
} Worker;
static void* run_worker(void* argument) {
    Worker* worker = argument;
    CHECK(KeTlsGetValue(worker->tls) == NULL);
    CHECK(KeTlsSetValue(worker->tls, worker));
    CHECK(!RtlTryEnterCriticalSection(worker->lock));
    CHECK(NtSetEvent(worker->event, NULL) == STATUS_SUCCESS);
    RtlEnterCriticalSection(worker->lock);
    worker->value = 42;
    RtlLeaveCriticalSection(worker->lock);
    CHECK(KeTlsGetValue(worker->tls) == worker);
    return NULL;
}
int main(void) {
    /* Guest storage can be compact and must not be overwritten by host locks. */
    uint32_t storage[4] = {0x11223344, 0x55667788, 0x99aabbcc, 0xddeeff00};
    uint32_t original[4]; memcpy(original, storage, sizeof(storage));
    RTL_CRITICAL_SECTION* lock = (RTL_CRITICAL_SECTION*)&storage[1];
    CHECK(RtlInitializeCriticalSection(lock) == STATUS_SUCCESS);
    CHECK(RtlInitializeCriticalSection(NULL) < 0);
    RtlEnterCriticalSection(lock);
    CHECK(RtlTryEnterCriticalSection(lock));
    RtlLeaveCriticalSection(lock);

    uint32_t slots[64];
    for (unsigned i = 0; i < 64; ++i) { slots[i] = KeTlsAlloc(); CHECK(slots[i] == i); }
    CHECK(KeTlsAlloc() == UINT32_MAX);
    CHECK(KeTlsSetValue(slots[0], storage));
    CHECK(KeTlsGetValue(slots[0]) == storage);
    CHECK(!KeTlsSetValue(64, storage));

    HANDLE event;
    CHECK(NtCreateEvent(&event, 0, NULL, NotificationEvent, 0) == STATUS_SUCCESS);
    LARGE_INTEGER poll = 0;
    CHECK(KeWaitForSingleObject(event, 0, 0, 0, &poll) == STATUS_TIMEOUT);
    Worker worker = {lock, event, slots[0], 0};
    HANDLE thread; uint32_t thread_id;
    CHECK(ExCreateThread(&thread, 65536, &thread_id, (void*)run_worker, &worker, 0) == STATUS_SUCCESS);
    LARGE_INTEGER deadline = -50000000; /* five seconds, never hang on failure */
    CHECK(KeWaitForSingleObject(event, 0, 0, 0, &deadline) == STATUS_SUCCESS);
    CHECK(KeWaitForSingleObject(event, 0, 0, 0, &poll) == STATUS_SUCCESS); /* manual reset */
    RtlLeaveCriticalSection(lock);
    CHECK(KeWaitForSingleObject(thread, 0, 0, 0, &deadline) == STATUS_SUCCESS);
    CHECK(worker.value == 42 && KeTlsGetValue(slots[0]) == storage);
    CHECK(KeResetEvent(event) == 1);
    CHECK(KeWaitForSingleObject(event, 0, 0, 0, &poll) == STATUS_TIMEOUT);
    CHECK(NtClose(thread) == STATUS_SUCCESS && NtClose(event) == STATUS_SUCCESS);

    CHECK(NtCreateEvent(&event, 0, NULL, SynchronizationEvent, 1) == STATUS_SUCCESS);
    CHECK(KeWaitForSingleObject(event, 0, 0, 0, &poll) == STATUS_SUCCESS);
    CHECK(KeWaitForSingleObject(event, 0, 0, 0, &poll) == STATUS_TIMEOUT); /* auto reset */
    CHECK(KeSetEvent(event, 0, 0) == 0 && KeSetEvent(event, 0, 0) == 1);
    CHECK(NtClose(event) == STATUS_SUCCESS);

    HANDLE semaphore; int32_t previous = -1;
    CHECK(NtCreateSemaphore(&semaphore, 0, NULL, 0, 2) == STATUS_SUCCESS);
    CHECK(KeWaitForSingleObject(semaphore, 0, 0, 0, &poll) == STATUS_TIMEOUT);
    CHECK(NtReleaseSemaphore(semaphore, 2, &previous) == STATUS_SUCCESS && previous == 0);
    CHECK(NtReleaseSemaphore(semaphore, 1, NULL) < 0); /* no counter overflow */
    CHECK(KeWaitForSingleObject(semaphore, 0, 0, 0, &poll) == STATUS_SUCCESS);
    CHECK(KeWaitForSingleObject(semaphore, 0, 0, 0, &poll) == STATUS_SUCCESS);
    CHECK(KeWaitForSingleObject(semaphore, 0, 0, 0, &poll) == STATUS_TIMEOUT);
    CHECK(NtClose(semaphore) == STATUS_SUCCESS);
    CHECK(NtWaitForSingleObjectEx(NULL, 0, 0, &poll) < 0);
    CHECK(sysThread_WaitTimeout(NULL, 0) == UINT32_MAX && hostGetLastError() == 6);

    uint32_t embedded[2] = {0x12345678, 0xabcdef01};
    KeInitializeEvent(embedded, SynchronizationEvent, 1);
    CHECK(NtWaitForSingleObjectEx(embedded, 1, 0, &poll) == STATUS_SUCCESS);
    CHECK(NtWaitForSingleObjectEx(embedded, 1, 0, &poll) == STATUS_TIMEOUT);
    CHECK(NtWaitForSingleObjectEx(embedded, 2, 0, &poll) == (NTSTATUS)STATUS_INVALID_PARAMETER);
    CHECK(NtWaitForSingleObjectEx(embedded, 1, 1, &poll) == STATUS_TIMEOUT); /* native alertable poll */
    CHECK(NtClose(embedded) == STATUS_SUCCESS);
    CHECK(embedded[0] == 0x12345678 && embedded[1] == 0xabcdef01);

    void* memory = MmAllocatePhysicalMemoryEx(0, 5000, 4, 0, UINT32_MAX, 8192);
    CHECK(memory && (uintptr_t)memory % 8192 == 0 && MmQueryAllocationSize(memory) == 8192);
    for (unsigned i = 0; i < 8192; ++i) CHECK(((unsigned char*)memory)[i] == 0);
    MmFreePhysicalMemory(0, memory);
    CHECK(MmQueryAllocationSize(memory) == 0);
    CHECK(!MmAllocatePhysicalMemoryEx(0, 5000, 4, 0, UINT32_MAX, 3));
    CHECK(RtlNtStatusToDosError(STATUS_SEMAPHORE_LIMIT_EXCEEDED) == 298);

    LARGE_INTEGER now; KeQuerySystemTime(&now);
    CHECK(now > 116444736000000000LL && KeQueryPerformanceFrequency() > 0);
    CHECK(KeDelayExecutionThread(0, 0, &now) == STATUS_SUCCESS); /* absolute past */
    LARGE_INTEGER delay = -10000;
    CHECK(KeDelayExecutionThread(0, 0, &delay) == STATUS_SUCCESS);
    KSPIN_LOCK spin = 0;
    KfLowerIrql(0);
    CHECK(KeRaiseIrqlToDpcLevel() == 0 && KeRaiseIrqlToDpcLevel() == 2);
    KfLowerIrql(0);
    CHECK(KeTryToAcquireSpinLockAtRaisedIrql(&spin));
    CHECK(!KeTryToAcquireSpinLockAtRaisedIrql(&spin));
    KeReleaseSpinLockFromRaisedIrql(&spin);
    for (unsigned i = 0; i < 64; ++i) CHECK(KeTlsFree(slots[i]));
    CHECK(!KeTlsFree(slots[0]));
    CHECK(RtlDeleteCriticalSection(lock) == STATUS_SUCCESS);
    CHECK(memcmp(storage, original, sizeof(storage)) == 0);
    puts("Win32 kernel synchronization tests passed (32-bit).");
    return 0;
}
