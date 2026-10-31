# Physics link wave G — completed and remaining

This pass addresses 20 of the 85 ABI entries supplied in `/tmp/tt-wave-G/physics.txt`.
It adds 32 original PPC routines (16 are dependencies absent from that list).
The 65 entries below were not addressed by this pass.

## Completed

- `0x82258A30` — `phArticulatedCollider_8A30`: shift every body's linear velocity
  relative to the root and rebuild angular/point velocity caches.
- `0x82258B10` — `phArticulatedCollider_8B10`: shift angular velocity, correct linear
  velocity by the position cross term, and rebuild the caches.
- `0x8224E668` — `phArticulatedCollider_E668`: RTTI cast, composite index resolution,
  and collider body-map lookup.
- `0x8228E750` — `rage::phBoundComposite_E750`: recursive descendant count.
- `0x8228F5C8` — `rage::phBoundComposite_ResolveBoundIndex`: map flattened descendant
  indices to immediate children. This dependency was named `pongCreatureInst_F5C8`
  in the symbol map; its receiver is a composite bound.
- `0x8228D0E8` — `phBound_TransformWorldCentroid`: enabled world-centroid cache,
  reusing the existing transform at `0x8228D1D0`.

Implementations: `src/physics/ph_physics.cpp` and `src/physics/bound_lookup.cpp`.
The new RTTI descriptor has a named definition in `src/physics/ld_ph_data.cpp`.
CMake includes the new lookup source.

## Consolidated names and signatures

- Both global mutable-pointer and `rage::` const-pointer declarations of each
  velocity setter now resolve to one global const-pointer declaration and lift.
- `phArticulatedCollider_E668_GetJointIndex` was a declared alias of `E668`;
  its caller now uses `phArticulatedCollider_E668` directly.
- No duplicate wrapper lift was added for those alternate spellings.

## Verification

- The two velocity specs and centroid-cache spec pass 600 trials on each of
  seeds 1 and 2. The three lookup specs pass 400 trials on each seed.
- Existing `ph_bound_transform_centroid` is checked separately on both seeds
  because the cache routine reuses it; its original PPC is executed transparently
  in the new cache spec.
- Velocity specs require exact finite float32 results; their `FTOL = 1e-99` only
  permits equivalent NaN encodings and signed zeros. Other new specs use no tolerance.
- All 24 deliberate mutations are caught as behavioral failures (11 velocity,
  10 lookup, 3 cache); build/spec errors and lift faults do not count.
- Native CMake configuration and compilation succeed. Linking still fails on
  remaining project symbols. None of the completed functions, alternate spellings,
  new lookup helper or descriptor appears in the final native linker errors.
- The local `tools/lift-check/.venv/` is a real Python 3.13 venv with Unicorn,
  created with the requested `uv` commands. The lift-check README is unchanged.
- Fixed a shared checker bug where nonzero tolerance accepted infinity against
  a finite value or opposite infinity. A selftest covers finite/nonfinite pairs,
  signed zero, NaNs and finite tolerance; restoring the old comparator produces
  15 regression failures. The velocity specs and their mutations pass with the
  stricter comparator.
- This is emulator and native-build verification, not console or gameplay testing.

Mutation runners live in `tools/lift-check/specs/`:
`_articulated_velocity_mutations.py`, `_bound_lookup_mutations.py`,
`_world_centroid_mutations.py`.

## Continuation — velocity limits and caller ABI

- `0x822560F8` — `phArticulatedCollider_60F8`: clamp linear/angular xyz speed,
  scale all four lanes, apply timestep damping, and rebuild cached velocities.
  Spec `ph_articulated_clamp_damp_velocities`: 800 trials on seeds 1 and 2.
- `0x82256B40` — `phArticulatedCollider_RestoreVelocities`: restore saved angular
  and point velocities, then recover origin linear velocity. This replaces the
  misleading declared-only name `phArticulatedCollider_RebuildJointWeights`.
  Spec `ph_articulated_restore_velocities`: 600 trials on both seeds.
- Re-lifted `SetTimestep` (`0x8224F040`) to pass linear limit, angular limit and
  timestep in the correct registers; retain the initial joint pointer through
  integration, then reload for later stages. Spec: 400 trials on both seeds.
- Corrected `PostIntegrate` (`0x8224EA28`) and the integration declaration to take
  and forward timestep; reload joint data between calls. Spec: 400 trials per seed.
- `_articulated_step_mutations.py` catches 11/11 mutations, and
  `_articulated_timestep_mutations.py` catches 4/4. All are behavioral failures.
- The native physics translation unit compiles with these changes.

## Continuation — joint clearing, propagation, and root rebasing

- `0x82255A40` — `phArticulatedCollider_ResetForceAccumulators`: clears current
  and saved body velocity vectors and calls each child joint's velocity-constraint
  reset. The historical name describes these fields poorly. Spec
  `ph_articulated_clear_velocities`: 400 trials on seeds 1 and 2.
- `0x82258450` — `phArticulatedCollider_8450`: calls child joints' motion
  propagation method, then rebuilds each affected body's angular/point velocity
  caches. Spec `ph_articulated_propagate_motion`: 400 trials per seed.
- `0x8224F0E0` — `phArticulatedCollider_F0E0`: publishes the root's transposed
  transform, adds its position to the collider origin, rebases all body positions,
  and adjusts cached point velocities. Root/collider aliasing is exercised.
  Spec `ph_articulated_rebase_from_root`: 600 trials per seed.
- `0x82126BD0` — `phArticulatedBody_ClearState`: zeros ten dynamic-state vectors
  on one body, preserving the intervening force block. This dependency was named
  `phArticulatedCollider_6BD0_2hr` in the symbol map. Spec
  `ph_articulated_body_clear_state`: 300 trials per seed.
- `0x822557F0` — `phArticulatedCollider_ResetJointChain`: clears dynamic state,
  restores each body's saved pose, rebuilds velocity caches, and clears per-body
  and per-child flags. Spec `ph_articulated_reset_joint_chain`: 600 trials per seed.
- `src/physics/articulated_joint.hpp` supplies a real virtual dispatch interface
  for propagation and constraint clearing; these lifts do not index vtables.
- `_articulated_joint_state_mutations.py` catches 13/13 behavioral mutations;
  `_articulated_chain_reset_mutations.py` catches 8/8.
- In this continuation, seven additional original routines and two existing
  callers were verified on both seeds, with 36/36 new mutations caught. Cumulative
  coverage is 13 newly lifted originals, 14 resolved input ABI entries, and 60
  caught mutations.
- Native compilation succeeds through linking. None of this continuation's
  completed symbols or renamed helpers remains in the native linker errors;
  unrelated unresolved symbols still prevent the executable from linking.
- Integration's declaration and callers were corrected in this continuation;
  its body, force preparation and solver rebuild are completed below.

## Continuation — complete articulated integration and solver math

The three requested hot entries are now implemented, including their previously
unlifted dependencies. These changes are in `src/physics/ph_physics.cpp`,
`src/rage/math/mat33.cpp`, `include/rage/mat33.hpp`, and the existing creature caller.

- `0x82256968` — `rage::ph_IntegrateJointPositions(void*, float)`: integrates all
  four position lanes, thresholds angular speed, normalizes the rotation axis with
  the VMX reciprocal refinement, and applies rotation * old basis.
- `0x82255FE0` — `phArticulatedCollider_5FE0`: resolves force responses, adds them
  to cached velocities, and recovers current angular/origin linear velocity.
- `0x82255D58` — `phArticulatedCollider_5D58`: builds spatial inertia, reduces child
  solvers backwards, applies parent state forwards, and inverts each body tensor.

Recovered helpers, all with their own seed-1/seed-2 specs:

- `0x82256D98` — `phArticulatedCollider_BuildRotation`: solver axis-angle matrix.
- `0x820C3BC8` — `rage::mat33ComposeInPlace`: shared basis composition. Replaces
  the declared-only `phJoint_3BC8_g`; `pongCreature::ReplayStarting` now calls the
  shared declaration and passes its existing spec on both seeds.
- `0x822556E0` — `phSpatialTensor_Multiply`: staged coupled-block vector product.
- `0x82256300` — `phArticulatedCollider_PrepareForceResponse`: local force response
  and backward/forward joint response virtuals.
- `0x82255F10` — `phSpatialTensor_Copy`: all twelve rows in vector-store order.
- `0x82255478` — `phSpatialTensor_Add`: nine coefficient rows, preserving padding.
- `0x82255558` — `phSpatialTensor_Difference`: staged negate/add in A/C/B order.
- `0x820D4F88` — `phMatrix_Multiply3x3`: basis product with original output W shuffles.
- `0x8225B7E0` — `phMatrix_InvertSymmetric`: lower-triangle cofactor inverse.
- `0x82350808` — `phMatrix_InvertRegularized`: strided inverse with trace-scaled pivots.
- `0x82259108` — `phMatrix_RotateDiagonal`: rotated diagonal inertia tensor.
- `0x82258E48` — `phArticulatedBody_BuildInertia`: mass, skew and parallel-axis terms.
- `0x8225B498` — `phSpatialTensor_Invert`: Schur-complement block inverse.

Verification and limits:

- All 16 new original routines pass seeds 1 and 2 (300–800 trials per spec).
- `ph_articulated_timestep_pipeline` additionally passes 96 trials per seed,
  executing the complete original pipeline with deterministic child-joint virtual
  models. Individual helper lifts are checked separately.
- `_articulated_integration_mutations.py` catches 11/11 mutations;
  `_articulated_force_mutations.py` catches 13/13;
  `_spatial_solver_mutations.py` catches 23/23, including the full pipeline case.
- The factored origin-velocity recovery keeps the earlier restore spec passing on
  both seeds. Native compilation succeeds; linking still fails on other symbols.
  These three hot entries, all new helpers, and `phJoint_3BC8_g` are absent from
  the final unresolved-symbol log.
- The original block inverse copies an uninitialized scratch fourth row into
  its output C block. The C++ lift preserves that unused destination padding
  instead of reading uninitialized C++ memory. Inverse, rebuild and pipeline
  specs ignore exactly that 16-byte fourth row per output tensor; every actual
  coefficient row and its W lane is compared. Other new specs ignore no bytes.
- VMX reciprocal accuracy is the harness model; this is not console evidence.
- Cumulative progress: 29 original routines lifted, 17/85 supplied ABI entries
  resolved, 107 deliberate mutations caught, and 68 input entries left.

## Continuation — constructor iterator and joint block initialization

- Corrected the existing `0x820C0170` vector constructor iterator to take a
  typed `(dst, stride, count, ctor)` callback contract. Its spec covers negative
  and zero counts, repeated destinations, reverse strides and callback effects.
- `phJointChain_Constructor` (`0x8225DD70`) now passes count 20 and the existing
  element constructor `atSingleton_E3F0_p44` (`0x8225E3F0`), rather than treating
  the constructor address as template data.
- `rage::phJoint3Dof_C4F8_w` (`0x821DC4F8`) now uses the named retail no-op
  `nop_8240E6D0`; the old raw address had the wrong high half.
- Its missing `phJoint3Dof_ResetAllJoints` spelling was the existing
  `util_4628` (`0x82154628`). Re-lifted the xyz defaults, flags and shared
  parameters and removed the declared alias. Three undefined scratch W words
  per active record are preserved; the specs ignore only those 12 bytes.
- Specs `lf_vector_ctor_iterator`, `ph_joint_block_reset`,
  `ph_joint_chain_constructor` and `ph_joint_four_block_constructor` pass seeds
  1 and 2 (400, 400, 40 and 200 trials respectively).
- `_joint_initialization_mutations.py` checks callback traversal, record writes,
  both element/block strides, counts, flags and reset dispatch; all 16 mutations are caught behaviorally.
- Native compilation succeeds; remaining unrelated symbols still prevent linking.

## Continuation — capsule inertia and hidden result ABI

- Replaced the zero-fill `ph_1B78` stub with `phCapsule_ComputeInertia`
  (`0x82411B78`): mass in f1, radius in f2, cylinder full length in f3,
  and diagonal inertia output in r6. Rounded products and fused sums match PPC.
  Constants are named image globals; there are no guest-address casts.
- Consolidated the two incorrect lifts of `0x822A3258` (`GetSupportPoint` and
  `GetExtents`) into `rage::phBoundCapsule::ComputeInertia`. The missing
  `ph_1B78_3` spelling was an incompatible declaration of that same core.
- Corrected `0x8233AD38` to `rage::phBoundTaperedCapsule::ComputeInertia`.
  Both shape methods return a three-float inertia vector: the PPC hidden result
  pointer is r3, receiver r4, and mass f1. Geometry loads are +70/+80 for the
  capsule and +70/+90 for the tapered variant.
- The third original direct caller, `0x822DE24C`, explicitly supplies r6 output
  independently of r3. The core therefore retains its r6 contract; r3-r5 are
  unused. No existing C++ implementation of that caller was found.
- Specs `ph_capsule_inertia`, `ph_bound_capsule_inertia` and
  `ph_bound_tapered_capsule_inertia` pass seeds 1 and 2 (600, 400, 400 trials).
  They cover sphere limit, zero/negative mass, degenerate/negative geometry,
  nonfinite values, overlapping shape/result and untouched W/guard words.
  Finite float32 comparisons are exact; equivalent NaNs/zeros are permitted.
- `_capsule_inertia_mutations.py` checks the old zero stub, mass, polynomial,
  fused rounding, per-axis scaling, geometry fields and wrapper arguments;
  all 14 mutations are caught behaviorally.
- Native compilation succeeds; these completed names are absent from the
  remaining link errors. This is emulator verification, not console testing.

## Continuation — angular displacement and body rotation

- Replaced the empty, misnamed `rage::phBoundCapsule_6C28_fw`
  (`0x82256C28`) with `phArticulatedCollider_ApplyAngularDisplacement`.
  It rotates each body, applies its position cross term and corrects cached
  point velocity using the original rounded VMX/scalar fused operations.
- Lifted `phArticulatedBody_Rotate` (`0x82258FC0`) using the existing normalized
  axis rotation and matrix composition lifts. Both four-lane transposes and
  the reciprocal refinement are retained. The cutoff also skips unordered
  squared length, matching PPC's `ble` branch.
- Corrected the caller at `0x8224FD50` to forward rotation vector r4 and read
  joint-data from confirmed offset +1D0. Removed missing `ph_ApplyAngularVelocity`
  declaration and the old no-argument caller spelling.
- Specs `ph_articulated_body_rotate`, `ph_articulated_apply_angular_displacement`
  and `ph_articulated_angular_displacement_caller` cover thresholds, nonfinite
  inputs, signed counts, repeated bodies, live vector aliases, matrix W writes,
  point corrections and all guards; all pass seeds 1 and 2
  (600 / 400 / 200 trials per seed).
  All finite float32 results compare exactly; NaN/zero encodings may differ.
- `_articulated_rotation_mutations.py` covers threshold, normalization,
  transposes, displacement/point signs, scalar fusion and caller dispatch;
  all 12 mutations are caught as behavioral failures.
- Reciprocal estimates follow the checker's true reciprocal; hardware estimate
  bits and FP exception flags remain outside this emulator proof.

## Remaining input entries (65)

Next gameplay targets confirmed in `.text.s` (not lifted in this batch):
The delta/reset helpers are `0x822577F0` / `0x82257918`, calling
`0x822571C8` / `0x82257368`. `phJoint_ApplyDelta` is `0x82257A30`; r6 is an output
matrix pointer, despite the current `int` declaration/caller parameter.

- `_phDemoWorld_67D0_g`
- `_ph_2E08`
- `_ph_5310`
- `_ph_7450`
- `_ph_A2A0`
- `_ph_D088`
- `_ph_DD28`
- `_ph_vt57D8_12_62F8`
- `_ph_vt5D38_15_0160`
- `_pongLookAtDriver_vfn_20`
- `_rage_14F0`
- `_sub_823517F8`
- `aud_2478(double)`
- `game_CE58(void*)`
- `phArticulatedCollider_ApplyJointDelta(void*, int, float const*)`
- `phArticulatedCollider_CreateJointConstraints(void*, unsigned int, unsigned int, unsigned int, unsigned int, unsigned int)`
- `phArticulatedCollider_ResetJointLink(void*, int)`
- `phBoundCapsule_ACB0_p45(void*)`
- `phBoundCapsule_ComputeAngleXZ(void*, float, float)`
- `phBoundCapsule_DecomposeRotation(float*, float*, float*, float*, float*)`
- `phBoundCapsule_GetJointAngle(void*)`
- `phBoundCapsule_ResolvePlayerIndex(void*)`
- `phBoundCapsule_SetupFromState(void*)`
- `phBoundCapsule_UpdateCapsuleState(void*)`
- `phBoundSphere_vfn_37(void*)`
- `phBound_LockChannel(void*, char const*, int)`
- `phCollider_CDF0_p39(void*)`
- `phCollider_RecalcBounds(void*)`
- `phCollider_vfn_1(void*)`
- `phCollider_vfn_42(void*)`
- `phDemoObject_Dtor(void*)`
- `phInst_8F10_p42(void*, unsigned int, void*, void*, void*, void*)`
- `phInst_AB00(rage::phInst*, void*, char const*)`
- `phInst_AC00_2hr(rage::phInst*)`
- `phJoint_ApplyDelta(void*, int, float const*, int)`
- `phObject::CreateViews(phObject*)`
- `phObject::ReleaseResources()`
- `phObject_4F28_p46(void*)`
- `phObject_BindOutputStream(void*, unsigned int, unsigned int, unsigned int, unsigned int, void*)`
- `phObject_ReleaseSavedField(void*)`
- `phObject_ReleaseStreamContext(void*)`
- `phObject_WriteValue(void*, unsigned int)`
- `ph_1EF8(void*, unsigned int, unsigned int, unsigned char*, unsigned int, unsigned char*, unsigned int, unsigned int)`
- `ph_3760(void*, void*, void*, int, int, int)`
- `ph_3760_4(void*, unsigned int, unsigned int, unsigned int)`
- `ph_9BC0(void*)`
- `ph_CollideShapeAgainstWorld(unsigned int, unsigned int, int, int)`
- `ph_DebugAssertPositive(char const*, double)`
- `ph_ProfilerBegin(char const*, int)`
- `ph_ResolveCollisionConstraint(unsigned int, unsigned int, void*)`
- `ph_Sqrtf_joint(rage::phJoint3Dof*, float)`
- `ph_TestCollisionPairDetailed(unsigned int, unsigned int, unsigned int, unsigned int, unsigned char*, unsigned int, unsigned char*, int)`
- `ph_ctor_FFD8(void*, void*)`
- `pongShadowMap_F010_g(void*, void*, void const*, void*)`
- `rage::phLevelNew_E648_wrh(rage::phQueryVector3 const*, rage::phQueryVector3 const*, rage::phQueryVector3 const*)`
- `rage_4CD0(void*)`
- `rage_A518(void*, void*, void*)`
- `rage_CopyChannelData(void*, unsigned int, void*)`
- `rmcDrawable_Init(void*)`
- `set_3348(void*, float)`
- `statePreInit_vfn_6(void*)`
- `thunk_fn_824885C8(void*)`
- `util_C788(void*)`
- `util_DA50(void*, void const*)`
- `util_F8E8(void*)`
