#pragma once
#include <stdint.h>
#include "platform/host_sync.h"

/* The Windows SDK stays in win32.c: its NT names, calling conventions and
 * CONTEXT are different from the Xbox kernel's public ABI. */
uint32_t tt_win_tls_alloc(void);
int tt_win_tls_free(uint32_t index);
void* tt_win_tls_get(uint32_t index);
int tt_win_tls_set(uint32_t index, void* value);
int32_t tt_win_create_event(void** handle, int manual, int signaled);
int32_t tt_win_set_event(void* handle, int32_t* previous);
int32_t tt_win_reset_event(void* handle, int32_t* previous);
int32_t tt_win_create_semaphore(void** handle, int32_t initial, int32_t maximum);
int32_t tt_win_release_semaphore(void* handle, int32_t count, int32_t* previous);
int32_t tt_win_wait(void* handle, int alertable, const int64_t* timeout);
int32_t tt_win_delay(int alertable, const int64_t* interval);
int32_t tt_win_close(void* handle);
int32_t tt_win_create_thread(void** handle, uint32_t stack, uint32_t* id,
                             void* start, void* parameter, uint32_t flags);
int32_t tt_win_terminate_thread(void* handle, int32_t status);
uint64_t tt_win_frequency(void);
int64_t tt_win_system_time(void);
void tt_win_yield(void);
int tt_win_spin_try(volatile uint32_t* lock);
void tt_win_spin_unlock(volatile uint32_t* lock);
