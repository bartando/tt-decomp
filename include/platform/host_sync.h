#pragma once

/* Host-only locks: never put this type in an image layout. */
typedef struct { void* state; } tt_mutex;
#define TT_MUTEX_INITIALIZER {0}
#ifdef __cplusplus
extern "C" {
#endif
void tt_mutex_lock(tt_mutex* mutex);
void tt_mutex_unlock(tt_mutex* mutex);
int tt_mutex_trylock(tt_mutex* mutex);
void tt_mutex_destroy(tt_mutex* mutex);
#ifdef __cplusplus
}
#endif
