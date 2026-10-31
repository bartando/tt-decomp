#pragma once

double crt_exp(double value); // @ 0x82432478
double crt_sin(double value); // @ 0x824301D8
double crt_cos(double value); // @ 0x824302B0
double crt_asin(double value); // @ 0x82430E88
double crt_atan2(double y, double x); // @ 0x82430FE0
double crt_fmod(double value, double divisor); // @ 0x82431D78

namespace rage {

// f2 is unused in the image; sigma arrives in f3.
float normalDensity(float value, float unused, float standardDeviation); // @ 0x821426B8

// Original double angle in f1; round cos/sin to float and store in that order.
// The two output pointers may alias (the final value is then sine).
void cosSin(float* cosine, float* sine, double angle);

} // namespace rage
