#include "xam/kernel.h"
#include "platform/host_sync.h"
#include <stdlib.h>

/* Some lifted objects reserve only eight bytes for a guest lock. A native
 * CRITICAL_SECTION/pthread mutex cannot live there. Key native recursive locks
 * by guest address, without overwriting neighbouring image fields. */
typedef struct CriticalSectionEntry {
    const void* address;
    tt_mutex mutex;
    struct CriticalSectionEntry* next;
} CriticalSectionEntry;
static tt_mutex registry_mutex = TT_MUTEX_INITIALIZER;
static CriticalSectionEntry* entries;

static tt_mutex* mutex_for(const void* address) {
    tt_mutex_lock(&registry_mutex);
    CriticalSectionEntry* entry = entries;
    while (entry && entry->address != address) entry = entry->next;
    if (!entry) {
        entry = calloc(1, sizeof(*entry));
        if (!entry) { tt_mutex_unlock(&registry_mutex); return NULL; }
        entry->address = address; entry->next = entries; entries = entry;
    }
    tt_mutex_unlock(&registry_mutex);
    return &entry->mutex;
}
NTSTATUS RtlInitializeCriticalSection(RTL_CRITICAL_SECTION* cs) {
    if (!cs) return STATUS_INVALID_PARAMETER;
    return mutex_for(cs) ? STATUS_SUCCESS : STATUS_NO_MEMORY;
}
void RtlEnterCriticalSection(RTL_CRITICAL_SECTION* cs) {
    if (cs) { tt_mutex* mutex = mutex_for(cs); if (!mutex) abort(); tt_mutex_lock(mutex); }
}
uint32_t RtlTryEnterCriticalSection(RTL_CRITICAL_SECTION* cs) {
    tt_mutex* mutex = cs ? mutex_for(cs) : NULL;
    return mutex && tt_mutex_trylock(mutex);
}
void RtlLeaveCriticalSection(RTL_CRITICAL_SECTION* cs) {
    if (cs) { tt_mutex* mutex = mutex_for(cs); if (!mutex) abort(); tt_mutex_unlock(mutex); }
}
NTSTATUS RtlDeleteCriticalSection(RTL_CRITICAL_SECTION* cs) {
    if (!cs) return STATUS_INVALID_PARAMETER;
    /* As on Win32, callers must ensure no thread owns or waits on the lock. */
    tt_mutex_lock(&registry_mutex);
    CriticalSectionEntry** link = &entries;
    while (*link && (*link)->address != cs) link = &(*link)->next;
    if (*link) {
        CriticalSectionEntry* entry = *link;
        *link = entry->next;
        tt_mutex_destroy(&entry->mutex); free(entry);
    }
    tt_mutex_unlock(&registry_mutex);
    return STATUS_SUCCESS;
}
