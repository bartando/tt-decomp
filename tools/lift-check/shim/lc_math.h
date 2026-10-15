/* Freestanding <math.h> for lift-check: the simple ones become instructions,
 * the rest stay calls that resolve to the game's copies via the symbol map. */
#pragma once
#ifdef __cplusplus
extern "C" {
#endif
float  sinf(float);   float  cosf(float);   float  tanf(float);
float  asinf(float);  float  acosf(float);  float  atanf(float);
float  atan2f(float, float);
float  expf(float);   float  logf(float);   float  log10f(float);
float  powf(float, float);  float fmodf(float, float);
double sin(double);   double cos(double);   double tan(double);
double asin(double);  double acos(double);  double atan(double);
double atan2(double, double);
double exp(double);   double log(double);   double log10(double);
double pow(double, double); double fmod(double, double);
#ifdef __cplusplus
}
#endif
static inline float  fabsf(float x)   { return __builtin_fabsf(x); }
static inline double fabs(double x)   { return __builtin_fabs(x); }
static inline float  sqrtf(float x)   { return __builtin_sqrtf(x); }
static inline double sqrt(double x)   { return __builtin_sqrt(x); }
static inline float  floorf(float x)  { return __builtin_floorf(x); }
static inline float  ceilf(float x)   { return __builtin_ceilf(x); }
static inline double floor(double x)  { return __builtin_floor(x); }
static inline double ceil(double x)   { return __builtin_ceil(x); }
static inline float  copysignf(float a, float b) { return __builtin_copysignf(a, b); }
static inline float  fminf(float a, float b) { return a < b ? a : b; }
static inline float  fmaxf(float a, float b) { return a > b ? a : b; }
#define HUGE_VALF __builtin_huge_valf()
#define HUGE_VAL  __builtin_huge_val()
#define INFINITY  __builtin_inff()
#define NAN       __builtin_nanf("")
#define M_PI      3.14159265358979323846
#define isnan(x)  __builtin_isnan(x)
#define isinf(x)  __builtin_isinf(x)
#define isfinite(x) __builtin_isfinite(x)
