#include "platform/host_sync.h"
#include <pthread.h>
#include <stdlib.h>

static pthread_mutex_t initialization_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t* native_mutex(tt_mutex* mutex) {
    pthread_mutex_lock(&initialization_lock);
    if (!mutex->state) {
        pthread_mutex_t* state = malloc(sizeof(*state));
        pthread_mutexattr_t attributes;
        if (!state || pthread_mutexattr_init(&attributes) != 0) abort();
        if (pthread_mutexattr_settype(&attributes, PTHREAD_MUTEX_RECURSIVE) != 0) abort();
        if (pthread_mutex_init(state, &attributes) != 0) abort();
        pthread_mutexattr_destroy(&attributes);
        mutex->state = state;
    }
    pthread_mutex_t* state = mutex->state;
    pthread_mutex_unlock(&initialization_lock);
    return state;
}
void tt_mutex_lock(tt_mutex* mutex) { if (pthread_mutex_lock(native_mutex(mutex)) != 0) abort(); }
void tt_mutex_unlock(tt_mutex* mutex) { if (pthread_mutex_unlock(native_mutex(mutex)) != 0) abort(); }
int tt_mutex_trylock(tt_mutex* mutex) { return pthread_mutex_trylock(native_mutex(mutex)) == 0; }
void tt_mutex_destroy(tt_mutex* mutex) {
    pthread_mutex_lock(&initialization_lock);
    if (mutex->state) {
        if (pthread_mutex_destroy(mutex->state) != 0) abort();
        free(mutex->state); mutex->state = NULL;
    }
    pthread_mutex_unlock(&initialization_lock);
}
