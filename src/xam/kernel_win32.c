/* Xbox kernel ABI over native Windows synchronization. SDK types and stdcall
 * imports are confined to platform/win32.c; guest exports remain cdecl. */
#include "xam/kernel.h"
#include "platform/win32.h"
#include <stddef.h>
#include <stdlib.h>

_Static_assert(sizeof(void*) == 4, "Xbox layouts require 32-bit pointers");
_Static_assert(sizeof(RTL_CRITICAL_SECTION) == 24, "Xbox critical section layout");
_Static_assert(offsetof(RTL_CRITICAL_SECTION, LockSemaphore) == 16, "Xbox critical section lock slot");

static tt_mutex tls_lock = TT_MUTEX_INITIALIZER;
static struct { uint32_t native; int allocated; } tls_slots[64];

/* KeInitializeEvent receives embedded guest storage, while NtCreateEvent
 * returns a native handle. Keep those representations behind one lookup. */
typedef struct EmbeddedEvent {
    void* storage;
    HANDLE handle;
    struct EmbeddedEvent* next;
} EmbeddedEvent;
static tt_mutex event_lock = TT_MUTEX_INITIALIZER;
static EmbeddedEvent* embedded_events;
static HANDLE event_handle(void* object) {
    tt_mutex_lock(&event_lock);
    EmbeddedEvent* entry = embedded_events;
    while (entry && entry->storage != object) entry = entry->next;
    HANDLE handle = entry ? entry->handle : object;
    tt_mutex_unlock(&event_lock);
    return handle;
}
void KeInitializeEvent(void* storage, EVENT_TYPE type, int32_t state) {
    if (!storage || (type != NotificationEvent && type != SynchronizationEvent)) return;
    HANDLE handle;
    if (tt_win_create_event(&handle, type == NotificationEvent, state != 0) < 0) abort();
    tt_mutex_lock(&event_lock);
    EmbeddedEvent* entry = embedded_events;
    while (entry && entry->storage != storage) entry = entry->next;
    if (!entry) {
        entry = malloc(sizeof(*entry));
        if (!entry) abort();
        entry->storage = storage; entry->next = embedded_events; embedded_events = entry;
    } else {
        tt_win_close(entry->handle);
    }
    entry->handle = handle;
    tt_mutex_unlock(&event_lock);
}

uint32_t KeTlsAlloc(void) {
    tt_mutex_lock(&tls_lock);
    for (uint32_t i = 0; i < 64; ++i) {
        if (!tls_slots[i].allocated) {
            uint32_t slot = tt_win_tls_alloc();
            if (slot == UINT32_MAX) break;
            tls_slots[i].native = slot; tls_slots[i].allocated = 1;
            tt_mutex_unlock(&tls_lock); return i;
        }
    }
    tt_mutex_unlock(&tls_lock); return UINT32_MAX;
}
uint32_t KeTlsFree(uint32_t index) {
    tt_mutex_lock(&tls_lock);
    int result = index < 64 && tls_slots[index].allocated && tt_win_tls_free(tls_slots[index].native);
    if (result) tls_slots[index].allocated = 0;
    tt_mutex_unlock(&tls_lock); return result;
}
void* KeTlsGetValue(uint32_t index) {
    tt_mutex_lock(&tls_lock);
    void* value = index < 64 && tls_slots[index].allocated ? tt_win_tls_get(tls_slots[index].native) : NULL;
    tt_mutex_unlock(&tls_lock); return value;
}
uint32_t KeTlsSetValue(uint32_t index, void* value) {
    tt_mutex_lock(&tls_lock);
    int result = index < 64 && tls_slots[index].allocated && tt_win_tls_set(tls_slots[index].native, value);
    tt_mutex_unlock(&tls_lock); return result;
}
NTSTATUS NtCreateEvent(HANDLE* handle, uint32_t access, void* attributes, uint32_t type, uint32_t state) {
    (void)access;
    if (handle) *handle = NULL;
    if (type > 1) return STATUS_INVALID_PARAMETER;
    if (attributes) return STATUS_NOT_SUPPORTED;
    return tt_win_create_event(handle, type == NotificationEvent, state != 0);
}
NTSTATUS NtSetEvent(HANDLE handle, int32_t* previous) { return tt_win_set_event(event_handle(handle), previous); }
NTSTATUS NtClearEvent(HANDLE handle) { return tt_win_reset_event(event_handle(handle), NULL); }
int32_t KeSetEvent(void* event, int32_t increment, uint32_t wait) {
    (void)increment; (void)wait;
    int32_t previous = 0; tt_win_set_event(event_handle(event), &previous); return previous;
}
int32_t KeResetEvent(void* event) {
    int32_t previous = 0; tt_win_reset_event(event_handle(event), &previous); return previous;
}
NTSTATUS KeWaitForSingleObject(void* object, uint32_t reason, uint32_t mode, uint32_t alertable, LARGE_INTEGER* timeout) {
    (void)reason; return NtWaitForSingleObjectEx(object, mode, alertable, timeout);
}
NTSTATUS NtWaitForSingleObjectEx(void* object, uint32_t mode, uint32_t alertable, const int64_t* timeout) {
    if (mode > 1) return STATUS_INVALID_PARAMETER;
    return tt_win_wait(event_handle(object), alertable, timeout);
}
NTSTATUS NtClose(HANDLE handle) {
    tt_mutex_lock(&event_lock);
    EmbeddedEvent** link = &embedded_events;
    while (*link && (*link)->storage != handle) link = &(*link)->next;
    if (*link) {
        EmbeddedEvent* entry = *link; *link = entry->next;
        handle = entry->handle; free(entry);
    }
    tt_mutex_unlock(&event_lock);
    return tt_win_close(handle);
}
NTSTATUS NtCreateSemaphore(HANDLE* handle, uint32_t access, void* attributes, int32_t initial, int32_t maximum) {
    (void)access;
    if (handle) *handle = NULL;
    if (initial < 0 || maximum <= 0 || initial > maximum) return STATUS_INVALID_PARAMETER;
    if (attributes) return STATUS_NOT_SUPPORTED;
    return tt_win_create_semaphore(handle, initial, maximum);
}
NTSTATUS NtReleaseSemaphore(HANDLE handle, int32_t count, int32_t* previous) {
    return tt_win_release_semaphore(handle, count, previous);
}

static __thread uint32_t critical_region_depth;
static __thread uint32_t current_irql;
void KeEnterCriticalRegion(void) { ++critical_region_depth; }
void KeLeaveCriticalRegion(void) { if (critical_region_depth) --critical_region_depth; }
uint32_t KeRaiseIrqlToDpcLevel(void) { uint32_t old = current_irql; current_irql = 2; return old; }
void KfLowerIrql(uint32_t irql) { current_irql = irql; }
void KeAcquireSpinLockAtRaisedIrql(KSPIN_LOCK* lock) { if (lock) while (!tt_win_spin_try(lock)) tt_win_yield(); }
void KeReleaseSpinLockFromRaisedIrql(KSPIN_LOCK* lock) { if (lock) tt_win_spin_unlock(lock); }
uint32_t KeTryToAcquireSpinLockAtRaisedIrql(KSPIN_LOCK* lock) { return lock && tt_win_spin_try(lock); }
uint64_t KeQueryPerformanceFrequency(void) { return tt_win_frequency(); }
void KeQuerySystemTime(LARGE_INTEGER* time) { if (time) *time = tt_win_system_time(); }
NTSTATUS NtYieldExecution(void) { tt_win_yield(); return STATUS_SUCCESS; }
NTSTATUS KeDelayExecutionThread(uint32_t mode, uint32_t alertable, LARGE_INTEGER* interval) {
    (void)mode; return tt_win_delay(alertable, interval);
}
NTSTATUS ExCreateThread(HANDLE* handle, uint32_t stack, uint32_t* id, void* start, void* parameter, uint32_t flags) {
    return tt_win_create_thread(handle, stack, id, start, parameter, flags);
}
NTSTATUS ExTerminateThread(HANDLE handle, NTSTATUS status) { return tt_win_terminate_thread(handle, status); }
