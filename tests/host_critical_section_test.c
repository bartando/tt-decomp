#include "xam/kernel.h"
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(value) do { if (!(value)) abort(); } while (0)
static uint32_t guest_storage[4] = {1, 2, 3, 4};
static int counter;
static RTL_CRITICAL_SECTION* lock = (RTL_CRITICAL_SECTION*)&guest_storage[1];
static void* worker(void* unused) {
    (void)unused;
    for (int i = 0; i < 10000; ++i) {
        RtlEnterCriticalSection(lock);
        CHECK(RtlTryEnterCriticalSection(lock));
        ++counter;
        RtlLeaveCriticalSection(lock);
        RtlLeaveCriticalSection(lock);
    }
    return NULL;
}
int main(void) {
    pthread_t threads[8];
    for (int i = 0; i < 8; ++i) CHECK(pthread_create(&threads[i], NULL, worker, NULL) == 0);
    for (int i = 0; i < 8; ++i) CHECK(pthread_join(threads[i], NULL) == 0);
    CHECK(counter == 80000);
    uint32_t original[4] = {1, 2, 3, 4};
    CHECK(memcmp(guest_storage, original, sizeof(original)) == 0);
    RtlDeleteCriticalSection(lock);
    puts("Host critical section recursion, contention and compact storage passed.");
}
