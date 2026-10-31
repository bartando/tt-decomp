#pragma once

double crt_sin(double value); // @ 0x824301D8
double crt_cos(double value); // @ 0x824302B0
double crt_asin(double value); // @ 0x82430E88
double crt_fmod(double value, double divisor); // @ 0x82431D78

namespace rage {

// Original double angle in f1; round cos/sin to float and store in that order.
// The two output pointers may alias (the final value is then sine).
void cosSin(float* cosine, float* sine, double angle);

} // namespace rage
