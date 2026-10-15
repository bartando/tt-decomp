#pragma once
/* Freestanding <time.h> for lift-check: declarations only. */
typedef long time_t;
typedef long clock_t;
#define CLOCKS_PER_SEC 1000000L
#ifdef __cplusplus
extern "C" {
#endif
time_t  time(time_t* out);
clock_t clock(void);
#ifdef __cplusplus
}
#endif
