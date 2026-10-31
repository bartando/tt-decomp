# Physics link wave G — completed and remaining

This pass addresses 8 of the 85 ABI entries supplied in `/tmp/tt-wave-G/physics.txt`.
It adds six original PPC routines (one is a dependency absent from that list).
The 77 entries below were not addressed by this pass.

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

## Remaining input entries (77)

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
- `phArticulatedCollider_5D58(void*)`
- `phArticulatedCollider_5FE0(void*)`
- `phArticulatedCollider_60F8(void*, float, float, float)`
- `phArticulatedCollider_8450(void*)`
- `phArticulatedCollider_ApplyJointDelta(void*, int, float const*)`
- `phArticulatedCollider_CreateJointConstraints(void*, unsigned int, unsigned int, unsigned int, unsigned int, unsigned int)`
- `phArticulatedCollider_F0E0(void*)`
- `phArticulatedCollider_RebuildJointWeights(void*)`
- `phArticulatedCollider_ResetForceAccumulators(void*)`
- `phArticulatedCollider_ResetJointChain(void*)`
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
- `phJoint3Dof_ResetAllJoints(rage::phJoint3Dof*, int)`
- `phJoint_ApplyDelta(void*, int, float const*, int)`
- `phObject::CreateViews(phObject*)`
- `phObject::ReleaseResources()`
- `phObject_4F28_p46(void*)`
- `phObject_BindOutputStream(void*, unsigned int, unsigned int, unsigned int, unsigned int, void*)`
- `phObject_ReleaseSavedField(void*)`
- `phObject_ReleaseStreamContext(void*)`
- `phObject_WriteValue(void*, unsigned int)`
- `ph_1B78_3(void*, float, float)`
- `ph_1EF8(void*, unsigned int, unsigned int, unsigned char*, unsigned int, unsigned char*, unsigned int, unsigned int)`
- `ph_3760(void*, void*, void*, int, int, int)`
- `ph_3760_4(void*, unsigned int, unsigned int, unsigned int)`
- `ph_9BC0(void*)`
- `ph_ApplyAngularVelocity(void*)`
- `ph_CollideShapeAgainstWorld(unsigned int, unsigned int, int, int)`
- `ph_DebugAssertPositive(char const*, double)`
- `ph_ProfilerBegin(char const*, int)`
- `ph_ResolveCollisionConstraint(unsigned int, unsigned int, void*)`
- `ph_Sqrtf_joint(rage::phJoint3Dof*, float)`
- `ph_TestCollisionPairDetailed(unsigned int, unsigned int, unsigned int, unsigned int, unsigned char*, unsigned int, unsigned char*, int)`
- `ph_ctor_FFD8(void*, void*)`
- `pongShadowMap_F010_g(void*, void*, void const*, void*)`
- `rage::phLevelNew_E648_wrh(rage::phQueryVector3 const*, rage::phQueryVector3 const*, rage::phQueryVector3 const*)`
- `rage::ph_IntegrateJointPositions(void*)`
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
