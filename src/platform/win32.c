#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winternl.h>
#include <stdlib.h>
#include "platform/win32.h"

/* These exports preserve NT relative/absolute 100ns timeouts and return codes,
 * including STATUS_USER_APC, without lossy millisecond conversions. */
__declspec(dllimport) NTSTATUS NTAPI NtSetEvent(HANDLE, PLONG);
__declspec(dllimport) NTSTATUS NTAPI NtResetEvent(HANDLE, PLONG);
__declspec(dllimport) NTSTATUS NTAPI NtReleaseSemaphore(HANDLE, LONG, PLONG);
__declspec(dllimport) NTSTATUS NTAPI NtDelayExecution(BOOLEAN, PLARGE_INTEGER);

static int32_t last_status(void) {
    switch (GetLastError()) {
    case ERROR_INVALID_HANDLE: return (int32_t)0xC0000008;
    case ERROR_NOT_ENOUGH_MEMORY: case ERROR_OUTOFMEMORY: return (int32_t)0xC0000017;
    case ERROR_ACCESS_DENIED: return (int32_t)0xC0000022;
    default: return (int32_t)0xC000000D;
    }
}

static CRITICAL_SECTION* native_mutex(tt_mutex* mutex) {
    CRITICAL_SECTION* state = InterlockedCompareExchangePointer(&mutex->state, NULL, NULL);
    if (!state) {
        CRITICAL_SECTION* candidate = malloc(sizeof(*candidate));
        if (!candidate) abort();
        InitializeCriticalSection(candidate);
        state = InterlockedCompareExchangePointer(&mutex->state, candidate, NULL);
        if (state) { DeleteCriticalSection(candidate); free(candidate); }
        else state = candidate;
    }
    return state;
}
void tt_mutex_lock(tt_mutex* mutex) { EnterCriticalSection(native_mutex(mutex)); }
void tt_mutex_unlock(tt_mutex* mutex) { LeaveCriticalSection(native_mutex(mutex)); }
int tt_mutex_trylock(tt_mutex* mutex) { return TryEnterCriticalSection(native_mutex(mutex)) != 0; }
void tt_mutex_destroy(tt_mutex* mutex) {
    CRITICAL_SECTION* state = InterlockedExchangePointer(&mutex->state, NULL);
    if (state) { DeleteCriticalSection(state); free(state); }
}
uint32_t tt_win_tls_alloc(void) { return TlsAlloc(); }
int tt_win_tls_free(uint32_t index) { return TlsFree(index) != 0; }
void* tt_win_tls_get(uint32_t index) { return TlsGetValue(index); }
int tt_win_tls_set(uint32_t index, void* value) { return TlsSetValue(index, value) != 0; }
int32_t tt_win_create_event(void** handle, int manual, int signaled) {
    if (!handle) return (int32_t)0xC000000D;
    *handle = CreateEventW(NULL, manual, signaled, NULL);
    return *handle ? 0 : last_status();
}
int32_t tt_win_set_event(void* handle, int32_t* previous) {
    LONG state;
    NTSTATUS status = NtSetEvent(handle, &state);
    if (status >= 0 && previous) *previous = state;
    return status;
}
int32_t tt_win_reset_event(void* handle, int32_t* previous) {
    LONG state;
    NTSTATUS status = NtResetEvent(handle, &state);
    if (status >= 0 && previous) *previous = state;
    return status;
}
int32_t tt_win_create_semaphore(void** handle, int32_t initial, int32_t maximum) {
    if (!handle || initial < 0 || maximum <= 0 || initial > maximum) return (int32_t)0xC000000D;
    *handle = CreateSemaphoreW(NULL, initial, maximum, NULL);
    return *handle ? 0 : last_status();
}
int32_t tt_win_release_semaphore(void* handle, int32_t count, int32_t* previous) {
    LONG old_count;
    NTSTATUS status = NtReleaseSemaphore(handle, count, &old_count);
    if (status >= 0 && previous) *previous = old_count;
    return status;
}
int32_t tt_win_wait(void* handle, int alertable, const int64_t* timeout) {
    LARGE_INTEGER time;
    if (timeout) time.QuadPart = *timeout;
    return NtWaitForSingleObject(handle, alertable != 0, timeout ? &time : NULL);
}
int32_t tt_win_delay(int alertable, const int64_t* interval) {
    if (!interval) return (int32_t)0xC000000D;
    LARGE_INTEGER time; time.QuadPart = *interval;
    return NtDelayExecution(alertable != 0, &time);
}
int32_t tt_win_close(void* handle) { return CloseHandle(handle) ? 0 : last_status(); }

typedef struct { void* (*start)(void*); void* parameter; } ThreadStart;
static DWORD WINAPI start_thread(void* parameter) {
    ThreadStart info = *(ThreadStart*)parameter;
    free(parameter);
    return (DWORD)(uintptr_t)info.start(info.parameter); // ptr32-check: host — Win32 thread exit code, not a stored game pointer.
}
int32_t tt_win_create_thread(void** handle, uint32_t stack, uint32_t* id,
                             void* start, void* parameter, uint32_t flags) {
    if (!handle || !start) return (int32_t)0xC000000D;
    /* Xbox bit 0 means suspended; Win32 uses CREATE_SUSPENDED (bit 2). */
    if (flags & ~1u) return (int32_t)0xC000000D;
    ThreadStart* info = malloc(sizeof(*info));
    if (!info) return (int32_t)0xC0000017;
    info->start = (void* (*)(void*))start; info->parameter = parameter;
    DWORD thread_id;
    *handle = CreateThread(NULL, stack, start_thread, info, (flags & 1) ? CREATE_SUSPENDED : 0, &thread_id);
    if (!*handle) { int32_t status = last_status(); free(info); return status; }
    if (id) *id = thread_id;
    return 0;
}
int32_t tt_win_terminate_thread(void* handle, int32_t status) {
    if (!TerminateThread(handle, (DWORD)status)) return last_status();
    WaitForSingleObject(handle, INFINITE);
    return tt_win_close(handle);
}
uint64_t tt_win_frequency(void) { LARGE_INTEGER value; QueryPerformanceFrequency(&value); return value.QuadPart; }
int64_t tt_win_system_time(void) {
    FILETIME value; GetSystemTimeAsFileTime(&value);
    return ((uint64_t)value.dwHighDateTime << 32) | value.dwLowDateTime;
}
void tt_win_yield(void) { if (!SwitchToThread()) Sleep(0); }
int tt_win_spin_try(volatile uint32_t* lock) { return InterlockedCompareExchange((volatile LONG*)lock, 1, 0) == 0; }
void tt_win_spin_unlock(volatile uint32_t* lock) { InterlockedExchange((volatile LONG*)lock, 0); }
