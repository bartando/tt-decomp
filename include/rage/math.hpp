#pragma once

namespace rage {

// Original double angle in f1; round cos/sin to float and store in that order.
// The two output pointers may alias (the final value is then sine).
void cosSin(float* cosine, float* sine, double angle);

} // namespace rage
