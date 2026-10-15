PPC_FUNC_IMPL(recomp_4C10_impl) {
	PPC_FUNC_PROLOGUE();
	uint32_t var_r24 = 0;
	uint32_t var_r20 = 0;
	uint32_t var_r19 = 0;
	uint32_t var_r21 = 0;
	uint32_t var_r23 = 0;
	uint32_t var_r17 = 0;
	uint32_t var_r22 = 0;
	uint32_t var_r18 = 0;
	uint32_t var_r25 = 0;
	uint32_t var_r26 = 0;
	uint32_t var_r29 = 0;
	uint32_t var_r27 = 0;
	uint32_t var_r28 = 0;
	uint32_t var_r30 = 0;
	uint32_t var_r31 = 0;
	// FRAME: size=496, savegprlr_17
	// mr r24,r3
	var_r24 = ctx.r3.u32;
	// mr r20,r4
	var_r20 = ctx.r4.u32;
	// lwz r11,4(r24)
	ctx.r11.u64 = PPC_LOAD_U32(var_r24 + 4);
	// cmplwi cr6,r11,0
	// beq cr6,0x82134e84
	if (ctx.r11.u32 != 0) {
		// lwz r19,0(r24)
		var_r19 = (uint32_t)(PPC_LOAD_U32(var_r24 + 0));
		// cmplwi cr6,r11,0
		// li r21,0
		var_r21 = 0;
		// li r23,-1
		var_r23 = (uint32_t)(-1);
		// li r17,0
		var_r17 = 0;
		// lwz r11,0(r19)
		ctx.r11.u64 = PPC_LOAD_U32(var_r19 + 0);
		// lwz r22,12(r11)
		var_r22 = (uint32_t)(PPC_LOAD_U32(ctx.r11.u32 + 12));
		// lwz r18,0(r11)
		var_r18 = (uint32_t)(PPC_LOAD_U32(ctx.r11.u32 + 0));
		// beq cr6,0x82134e10
		if (ctx.r11.u32 != 0) {
			// li r25,0
			var_r25 = 0;
		loc_82134C58:
			// lwz r11,0(r24)
			ctx.r11.u64 = PPC_LOAD_U32(var_r24 + 0);
			// li r26,0
			var_r26 = 0;
			// lwzx r29,r25,r11
			var_r29 = (uint32_t)(PPC_LOAD_U32(var_r25 + ctx.r11.u32));
			// lwz r10,0(r29)
			ctx.r10.u64 = PPC_LOAD_U32(var_r29 + 0);
			// lwz r27,12(r29)
			var_r27 = (uint32_t)(PPC_LOAD_U32(var_r29 + 12));
			// cmpw cr6,r10,r18
			// bne cr6,0x82134da0
			if (ctx.r10.s32 == (int32_t)var_r18) {
				// clrlwi r28,r27,31
				var_r28 = (uint32_t)(var_r27 & 0x1);
				// clrlwi r9,r22,31
				ctx.r9.u64 = var_r22 & 0x1;
				// cmplw cr6,r9,r28
				// bne cr6,0x82134da0
				if (ctx.r9.u32 != var_r28) goto loc_82134DA0;
				// addi r10,r1,80
				ctx.r10.s64 = ctx.r1.s64 + 80;
				// mr r11,r20
				ctx.r11.u64 = var_r20;
				// li r9,34
				ctx.r9.s64 = 34;
				// mtctr r9
				ctx.ctr.u64 = ctx.r9.u64;
			loc_82134C94:
				// lwz r8,0(r11)
				ctx.r8.u64 = PPC_LOAD_U32(ctx.r11.u32 + 0);
				// addi r11,r11,4
				ctx.r11.s64 = ctx.r11.s64 + 4;
				// stw r8,0(r10)
				PPC_STORE_U32(ctx.r10.u32 + 0, ctx.r8.u32);
				// addi r10,r10,4
				ctx.r10.s64 = ctx.r10.s64 + 4;
				// bdnz 0x82134c94
				--ctx.ctr.u64;
				if (ctx.ctr.u32 != 0) goto loc_82134C94;
				// cmplwi cr6,r27,0
				// beq cr6,0x82134cdc
				if (var_r27 != 0) {
					// li r30,0
					var_r30 = 0;
					// mr r31,r27
					var_r31 = (uint32_t)(var_r27);
				loc_82134CB8:
					// lwz r7,16(r29)
					ctx.r7.u64 = PPC_LOAD_U32(var_r29 + 16);
					// li r4,2
					ctx.r4.s64 = 2;
					// addi r3,r1,80
					ctx.r3.s64 = ctx.r1.s64 + 80;
					// lhzx r5,r7,r30
					ctx.r5.u64 = PPC_LOAD_U16(ctx.r7.u32 + var_r30);
					// bl 0x821357b8
					cmOperatorCtor_57B8_w(ctx, base);
					// addi r31,r31,-1
					var_r31 = (uint32_t)(var_r31 + -1);
					// addi r30,r30,2
					var_r30 = (uint32_t)(var_r30 + 2);
					// cmplwi cr6,r31,0
					// bne cr6,0x82134cb8
					if (var_r31 != 0) goto loc_82134CB8;
				}
			loc_82134CDC:
				// cmplwi cr6,r28,0
				// bne cr6,0x82134d78
				if (var_r28 == 0) {
					// addi r10,r1,224
					ctx.r10.s64 = ctx.r1.s64 + 224;
					// mr r11,r20
					ctx.r11.u64 = var_r20;
					// li r9,34
					ctx.r9.s64 = 34;
					// mtctr r9
					ctx.ctr.u64 = ctx.r9.u64;
				loc_82134CF4:
					// lwz r6,0(r11)
					ctx.r6.u64 = PPC_LOAD_U32(ctx.r11.u32 + 0);
					// addi r11,r11,4
					ctx.r11.s64 = ctx.r11.s64 + 4;
					// stw r6,0(r10)
					PPC_STORE_U32(ctx.r10.u32 + 0, ctx.r6.u32);
					// addi r10,r10,4
					ctx.r10.s64 = ctx.r10.s64 + 4;
					// bdnz 0x82134cf4
					--ctx.ctr.u64;
					if (ctx.ctr.u32 != 0) goto loc_82134CF4;
					// lwz r11,12(r29)
					ctx.r11.u64 = PPC_LOAD_U32(var_r29 + 12);
					// addi r31,r11,-1
					var_r31 = (uint32_t)(ctx.r11.s64 + -1);  // addr:0x8201ffff
					// cmpwi cr6,r31,0
					// blt cr6,0x82134d40
					if ((int32_t)var_r31 >= 0) {
						// rlwinm r30,r31,1,0,30
						var_r30 = (uint32_t)(__builtin_rotateleft64(var_r31 | (var_r31 << 32), 1) & 0xFFFFFFFE);
					loc_82134D1C:
						// lwz r5,16(r29)
						ctx.r5.u64 = PPC_LOAD_U32(var_r29 + 16);
						// li r4,2
						ctx.r4.s64 = 2;
						// addi r3,r1,224
						ctx.r3.s64 = ctx.r1.s64 + 224;
						// lhzx r5,r5,r30
						ctx.r5.u64 = PPC_LOAD_U16(ctx.r5.u32 + var_r30);
						// bl 0x821357b8
						cmOperatorCtor_57B8_w(ctx, base);
						// addi r31,r31,-1
						var_r31 = (uint32_t)(var_r31 + -1);
						// addi r30,r30,-2
						var_r30 = (uint32_t)(var_r30 + -2);
						// cmpwi cr6,r31,0
						// bge cr6,0x82134d1c
						if ((int32_t)var_r31 >= 0) goto loc_82134D1C;
					}
				loc_82134D40:
					// lwz r4,224(r1)
					ctx.r4.u64 = PPC_LOAD_U32(ctx.r1.u32 + 224);
					// lwz r3,80(r1)
					ctx.r3.u64 = PPC_LOAD_U32(ctx.r1.u32 + 80);
					// cmpw cr6,r4,r3
					// ble cr6,0x82134d78
					if (ctx.r4.s32 <= ctx.r3.s32) goto loc_82134D78;
					// addi r10,r1,80
					ctx.r10.s64 = ctx.r1.s64 + 80;
					// addi r11,r1,224
					ctx.r11.s64 = ctx.r1.s64 + 224;
					// li r9,34
					ctx.r9.s64 = 34;
					// mtctr r9
					ctx.ctr.u64 = ctx.r9.u64;
				loc_82134D60:
					// lwz r9,0(r11)
					ctx.r9.u64 = PPC_LOAD_U32(ctx.r11.u32 + 0);
					// addi r11,r11,4
					ctx.r11.s64 = ctx.r11.s64 + 4;
					// stw r9,0(r10)
					PPC_STORE_U32(ctx.r10.u32 + 0, ctx.r9.u32);
					// addi r10,r10,4
					ctx.r10.s64 = ctx.r10.s64 + 4;
					// bdnz 0x82134d60
					--ctx.ctr.u64;
					if (ctx.ctr.u32 != 0) goto loc_82134D60;
					// li r26,1
					var_r26 = 1;
				}
			loc_82134D78:
				// lwz r8,0(r20)
				ctx.r8.u64 = PPC_LOAD_U32(var_r20 + 0);
				// lwz r7,80(r1)
				ctx.r7.u64 = PPC_LOAD_U32(ctx.r1.u32 + 80);
				// subf r10,r8,r7
				ctx.r10.s64 = ctx.r7.s64 - ctx.r8.s64;
				// cmpw cr6,r10,r23
				// ble cr6,0x82134da0
				if (ctx.r10.s32 <= (int32_t)var_r23) goto loc_82134DA0;
				// lwz r11,0(r24)
				ctx.r11.u64 = PPC_LOAD_U32(var_r24 + 0);
				// mr r23,r10
				var_r23 = ctx.r10.u32;
				// mr r22,r27
				var_r22 = (uint32_t)(var_r27);
				// add r19,r25,r11
				var_r19 = (uint32_t)(var_r25 + ctx.r11.u64);
				// mr r21,r26
				var_r21 = (uint32_t)(var_r26);
			}
		loc_82134DA0:
			// lwz r6,4(r24)
			ctx.r6.u64 = PPC_LOAD_U32(var_r24 + 4);
			// addi r17,r17,1
			var_r17 = (uint32_t)(var_r17 + 1);
			// addi r25,r25,4
			var_r25 = (uint32_t)(var_r25 + 4);
			// cmplw cr6,r17,r6
			// blt cr6,0x82134c58
			if (var_r17 < ctx.r6.u32) goto loc_82134C58;
			// cmpwi cr6,r21,0
			// beq cr6,0x82134e10
			if ((int32_t)var_r21 == 0) goto loc_82134E10;
			// lwz r5,0(r19)
			ctx.r5.u64 = PPC_LOAD_U32(var_r19 + 0);
			// li r8,0
			ctx.r8.s64 = 0;
			// lwz r11,12(r5)
			ctx.r11.u64 = PPC_LOAD_U32(ctx.r5.u32 + 12);
			// addi r10,r11,-1
			ctx.r10.s64 = ctx.r11.s64 + -1;
			// cmpwi cr6,r10,0
			// ble cr6,0x82134e10
			if (ctx.r10.s32 <= 0) goto loc_82134E10;
			// rlwinm r11,r10,1,0,30
			ctx.r11.u64 = __builtin_rotateleft64(ctx.r10.u32 | (ctx.r10.u64 << 32), 1) & 0xFFFFFFFE;
			// li r9,0
			ctx.r9.s64 = 0;
		loc_82134DDC:
			// lwz r7,16(r5)
			ctx.r7.u64 = PPC_LOAD_U32(ctx.r5.u32 + 16);
			// addi r8,r8,1
			ctx.r8.s64 = ctx.r8.s64 + 1;
			// addi r10,r10,-1
			ctx.r10.s64 = ctx.r10.s64 + -1;
			// add r6,r9,r7
			ctx.r6.u64 = ctx.r9.u64 + ctx.r7.u64;
			// addi r9,r9,2
			ctx.r9.s64 = ctx.r9.s64 + 2;
			// cmpw cr6,r8,r10
			// lhzx r4,r11,r7
			ctx.r4.u64 = PPC_LOAD_U16(ctx.r11.u32 + ctx.r7.u32);
			// lhz r7,0(r6)
			ctx.r7.u64 = PPC_LOAD_U16(ctx.r6.u32 + 0);
			// sth r4,0(r6)
			PPC_STORE_U16(ctx.r6.u32 + 0, ctx.r4.u16);
			// lwz r3,16(r5)
			ctx.r3.u64 = PPC_LOAD_U32(ctx.r5.u32 + 16);
			// sthx r7,r3,r11
			PPC_STORE_U16(ctx.r3.u32 + ctx.r11.u32, ctx.r7.u16);
			// addi r11,r11,-2
			ctx.r11.s64 = ctx.r11.s64 + -2;
			// blt cr6,0x82134ddc
			if (ctx.r8.s32 < ctx.r10.s32) goto loc_82134DDC;
		}
	loc_82134E10:
		// lwz r10,4(r24)
		ctx.r10.u64 = PPC_LOAD_U32(var_r24 + 4);
		// cmplwi cr6,r10,0
		// beq cr6,0x82134e24
		if (ctx.r10.u32 != 0) {
			// lwz r11,0(r24)
			ctx.r11.u64 = PPC_LOAD_U32(var_r24 + 0);
			// b 0x82134e28
		} else {
		loc_82134E24:
			// li r11,0
			ctx.r11.s64 = 0;
		}
	loc_82134E28:
		// cmplw cr6,r19,r11
		// beq cr6,0x82134e6c
		if (var_r19 != ctx.r11.u32) {
			// lwz r9,0(r19)
			ctx.r9.u64 = PPC_LOAD_U32(var_r19 + 0);
			// cmplwi cr6,r10,0
			// beq cr6,0x82134e44
			if (ctx.r10.u32 != 0) {
				// lwz r11,0(r24)
				ctx.r11.u64 = PPC_LOAD_U32(var_r24 + 0);
				// b 0x82134e48
			} else {
			loc_82134E44:
				// li r11,0
				ctx.r11.s64 = 0;
			}
		loc_82134E48:
			// lwz r11,0(r11)
			ctx.r11.u64 = PPC_LOAD_U32(ctx.r11.u32 + 0);
			// stw r11,0(r19)
			PPC_STORE_U32(var_r19 + 0, ctx.r11.u32);
			// lwz r10,4(r24)
			ctx.r10.u64 = PPC_LOAD_U32(var_r24 + 4);
			// cmplwi cr6,r10,0
			// beq cr6,0x82134e64
			if (ctx.r10.u32 != 0) {
				// lwz r11,0(r24)
				ctx.r11.u64 = PPC_LOAD_U32(var_r24 + 0);
				// b 0x82134e68
			} else {
			loc_82134E64:
				// li r11,0
				ctx.r11.s64 = 0;
			}
		loc_82134E68:
			// stw r9,0(r11)
			PPC_STORE_U32(ctx.r11.u32 + 0, ctx.r9.u32);
		}
	loc_82134E6C:
		// lwz r9,4(r24)
		ctx.r9.u64 = PPC_LOAD_U32(var_r24 + 4);
		// cmplwi cr6,r9,0
		// beq cr6,0x82134e84
		if (ctx.r9.u32 == 0) {
			// li r3,0
			ctx.r3.s64 = 0;
			return;
		}
		// lwz r3,0(r24)
		ctx.r3.u64 = PPC_LOAD_U32(var_r24 + 0);
		return;
	}
loc_82134E84:
	// li r3,0
	ctx.r3.s64 = 0;
	return;
}

