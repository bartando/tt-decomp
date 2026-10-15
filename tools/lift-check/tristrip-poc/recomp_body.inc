PPC_FUNC_IMPL(cmOperatorCtor_42A0_w) {
	PPC_FUNC_PROLOGUE();
	uint32_t var_r31 = 0;
	uint32_t var_r30 = 0;
	uint32_t var_r26 = 0;
	uint32_t var_r27 = 0;
	uint32_t var_r28 = 0;
	uint32_t var_r29 = 0;
	// FRAME: size=144, savegprlr_26
	// mr r31,r3
	var_r31 = ctx.r3.u32;
	// lis r11,16383
	ctx.r11.s64 = 1073676288;
	// mr r30,r5
	var_r30 = ctx.r5.u32;
	// ori r10,r11,65535
	ctx.r10.u64 = ctx.r11.u64 | 65535;
	// li r26,-1
	var_r26 = (uint32_t)(-1);
	// cmplw cr6,r4,r10
	// stw r4,4(r31)
	PPC_STORE_U32(var_r31 + 4, ctx.r4.u32);
	// rlwinm r27,r4,2,0,29
	var_r27 = (uint32_t)(__builtin_rotateleft64(ctx.r4.u32 | (ctx.r4.u64 << 32), 2) & 0xFFFFFFFC);
	// ble cr6,0x821342d4
	if (ctx.r4.u32 > ctx.r10.u32) {
		// mr r27,r26
		var_r27 = (uint32_t)(var_r26);
	}
loc_821342D4:
	// bl 0x820c0038
	xe_main_thread_init_0038(ctx, base);
	// lwz r28,0(r13)
	var_r28 = (uint32_t)(PPC_LOAD_U32(ctx.r13.u32 + 0)  /* SDA:0x82600000 */);
	// li r29,4
	var_r29 = 4;
	// li r5,16
	ctx.r5.s64 = 16;
	// mr r4,r27
	ctx.r4.u64 = var_r27;
	// lwzx r3,r29,r28
	ctx.r3.u64 = PPC_LOAD_U32(var_r29 + var_r28);
	// lwz r8,4(r9)
	// bctrl
	VCALL(ctx.r3.u32, 1, ctx, base);  // vtable slot 1 (byte +4)
	// lis r7,32767
	ctx.r7.s64 = 2147418112;
	// stw r30,12(r31)
	PPC_STORE_U32(var_r31 + 12, var_r30);
	// ori r6,r7,65535
	ctx.r6.u64 = ctx.r7.u64 | 65535;
	// stw r3,8(r31)
	PPC_STORE_U32(var_r31 + 8, ctx.r3.u32);
	// cmplw cr6,r30,r6
	// rlwinm r30,r30,1,0,30
	bool harness_gt = var_r30 > ctx.r6.u32;  // HARNESS: recomp compared after the shift
	var_r30 = (uint32_t)(__builtin_rotateleft64(var_r30 | (var_r30 << 32), 1) & 0xFFFFFFFE);
	// ble cr6,0x8213431c
	if (harness_gt) {
		// mr r30,r26
		var_r30 = (uint32_t)(var_r26);
	}
loc_8213431C:
	// bl 0x820c0038
	xe_main_thread_init_0038(ctx, base);
	// lwzx r3,r29,r28
	ctx.r3.u64 = PPC_LOAD_U32(var_r29 + var_r28);
	// li r5,16
	ctx.r5.s64 = 16;
	// mr r4,r30
	ctx.r4.u64 = var_r30;
	// lwz r10,4(r11)
	// bctrl
	VCALL(ctx.r3.u32, 1, ctx, base);  // vtable slot 1 (byte +4)
	// mr r9,r3
	ctx.r9.u64 = ctx.r3.u64;
	// mr r3,r31
	ctx.r3.u64 = var_r31;
	// stw r9,16(r31)
	PPC_STORE_U32(var_r31 + 16, ctx.r9.u32);
	return;
}

PPC_FUNC_IMPL(cmOperatorCtor_4E90_w) {
	PPC_FUNC_PROLOGUE();
	uint32_t var_r24 = 0;
	uint32_t var_r22 = 0;
	uint32_t var_r31 = 0;
	uint32_t var_r23 = 0;
	uint32_t var_r26 = 0;
	uint32_t var_r27 = 0;
	uint32_t var_r29 = 0;
	uint32_t var_r28 = 0;
	uint32_t var_r30 = 0;
	uint32_t var_r25 = 0;
	// FRAME: size=304, savegprlr_22
	// mr r24,r4
	var_r24 = ctx.r4.u32;
	// mr r22,r5
	var_r22 = ctx.r5.u32;
	// lwz r11,4(r24)
	ctx.r11.u64 = PPC_LOAD_U32(var_r24 + 4);
	// rlwinm r10,r11,1,0,30
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 1) & 0xFFFFFFFE;
	// cmplwi cr6,r11,0
	// add r10,r11,r10
	ctx.r10.u64 = ctx.r11.u64 + ctx.r10.u64;
	// addi r9,r10,2
	ctx.r9.s64 = ctx.r10.s64 + 2;
	// beq cr6,0x82134edc
	if (ctx.r11.u32 != 0) {
		// lwz r10,0(r24)
		ctx.r10.u64 = PPC_LOAD_U32(var_r24 + 0);
	loc_82134EC0:
		// lwz r8,0(r10)
		ctx.r8.u64 = PPC_LOAD_U32(ctx.r10.u32 + 0);
		// addi r11,r11,-1
		ctx.r11.s64 = ctx.r11.s64 + -1;
		// addi r10,r10,4
		ctx.r10.s64 = ctx.r10.s64 + 4;
		// cmplwi cr6,r11,0
		// lwz r8,12(r8)
		ctx.r8.u64 = PPC_LOAD_U32(ctx.r8.u32 + 12);
		// add r9,r8,r9
		ctx.r9.u64 = ctx.r8.u64 + ctx.r9.u64;
		// bne cr6,0x82134ec0
		if (ctx.r11.u32 != 0) goto loc_82134EC0;
	}
loc_82134EDC:
	// lis r7,32767
	ctx.r7.s64 = 2147418112;
	// rlwinm r31,r9,1,0,30
	var_r31 = (uint32_t)(__builtin_rotateleft64(ctx.r9.u32 | (ctx.r9.u64 << 32), 1) & 0xFFFFFFFE);
	// ori r6,r7,65535
	ctx.r6.u64 = ctx.r7.u64 | 65535;
	// cmplw cr6,r9,r6
	// ble cr6,0x82134ef4
	if (ctx.r9.u32 > ctx.r6.u32) {
		// li r31,-1
		var_r31 = (uint32_t)(-1);
	}
loc_82134EF4:
	// bl 0x820c0038
	xe_main_thread_init_0038(ctx, base);
	// lwz r3,0(r13)
	ctx.r3.u64 = PPC_LOAD_U32(ctx.r13.u32 + 0)  /* SDA:0x82600000 */;
	// li r11,4
	ctx.r11.s64 = 4;
	// li r5,16
	ctx.r5.s64 = 16;
	// mr r4,r31
	ctx.r4.u64 = var_r31;
	// lwzx r3,r11,r3
	ctx.r3.u64 = PPC_LOAD_U32(ctx.r11.u32 + ctx.r3.u32);
	// lwz r9,4(r10)
	// bctrl
	VCALL(ctx.r3.u32, 1, ctx, base);  // vtable slot 1 (byte +4)
	// li r23,0
	var_r23 = 0;
	// mr r26,r3
	var_r26 = ctx.r3.u32;
	// mr r31,r23
	var_r31 = (uint32_t)(var_r23);
	// addi r11,r1,84
	ctx.r11.s64 = ctx.r1.s64 + 84;
	// li r9,-1
	ctx.r9.s64 = -1;  // HARNESS: recomp dropped this
	// stw r23,192(r1)
	PPC_STORE_U32(ctx.r1.u32 + 192, var_r23);
	// li r10,9
	ctx.r10.s64 = 9;
	// stw r23,80(r1)
	PPC_STORE_U32(ctx.r1.u32 + 80, var_r23);
	// mtctr r10
	ctx.ctr.u64 = ctx.r10.u64;
loc_82134F40:
	// stw r9,0(r11)
	PPC_STORE_U32(ctx.r11.u32 + 0, ctx.r9.u32);
	// addi r11,r11,4
	ctx.r11.s64 = ctx.r11.s64 + 4;
	// bdnz 0x82134f40
	--ctx.ctr.u64;
	if (ctx.ctr.u32 != 0) goto loc_82134F40;
	// lwz r8,4(r24)
	ctx.r8.u64 = PPC_LOAD_U32(var_r24 + 4);
	// cmplwi cr6,r8,0
	// beq cr6,0x82134f60
	if (ctx.r8.u32 != 0) {
		// lwz r27,0(r24)
		var_r27 = (uint32_t)(PPC_LOAD_U32(var_r24 + 0));
		// b 0x82134f64
	} else {
	loc_82134F60:
		// mr r27,r23
		var_r27 = (uint32_t)(var_r23);
	}
loc_82134F64:
	// lwz r29,0(r27)
	var_r29 = (uint32_t)(PPC_LOAD_U32(var_r27 + 0));
	// mr r28,r23
	var_r28 = (uint32_t)(var_r23);
	// lwz r7,12(r29)
	ctx.r7.u64 = PPC_LOAD_U32(var_r29 + 12);
	// cmplwi cr6,r7,0
	// ble cr6,0x82134fb4
	if (ctx.r7.u32 > 0) {
		// mr r30,r23
		var_r30 = (uint32_t)(var_r23);
	loc_82134F7C:
		// lwz r6,16(r29)
		ctx.r6.u64 = PPC_LOAD_U32(var_r29 + 16);
		// li r4,1
		ctx.r4.s64 = 1;
		// addi r3,r1,80
		ctx.r3.s64 = ctx.r1.s64 + 80;
		// addi r31,r31,1
		var_r31 = (uint32_t)(var_r31 + 1);
		// lhzx r5,r30,r6
		ctx.r5.u64 = PPC_LOAD_U16(var_r30 + ctx.r6.u32);
		// sthx r5,r30,r26
		PPC_STORE_U16(var_r30 + var_r26, ctx.r5.u16);
		// lwz r11,16(r29)
		ctx.r11.u64 = PPC_LOAD_U32(var_r29 + 16);
		// lhzx r5,r30,r11
		ctx.r5.u64 = PPC_LOAD_U16(var_r30 + ctx.r11.u32);
		// bl 0x821357b8
		cmOperatorCtor_57B8_w(ctx, base);
		// lwz r10,12(r29)
		ctx.r10.u64 = PPC_LOAD_U32(var_r29 + 12);
		// addi r28,r28,1
		var_r28 = (uint32_t)(var_r28 + 1);
		// addi r30,r30,2
		var_r30 = (uint32_t)(var_r30 + 2);
		// cmplw cr6,r28,r10
		// blt cr6,0x82134f7c
		if (var_r28 < ctx.r10.u32) goto loc_82134F7C;
	}
loc_82134FB4:
	// mr r4,r27
	ctx.r4.u64 = var_r27;
	// mr r3,r24
	ctx.r3.u64 = var_r24;
	// bl 0x82134350
	pongNetMessageHolder_4350_wrh(ctx, base);
	// lwz r9,4(r24)
	ctx.r9.u64 = PPC_LOAD_U32(var_r24 + 4);
	// cmplwi cr6,r9,0
	// beq cr6,0x821350a8
ctx.r3.u64 = ctx.r9.u64;  // HARNESS: asm tests r9 on entry, recomp tested r3
while (ctx.r3.u32 != 0) {
	loc_82134FCC:
		// addi r4,r1,80
		ctx.r4.s64 = ctx.r1.s64 + 80;
		// mr r3,r24
		ctx.r3.u64 = var_r24;
		// bl 0x82134c10
		cmOperatorCtor_4C10_wrh(ctx, base);
		// mr r25,r3
		var_r25 = ctx.r3.u32;
		// rlwinm r11,r31,1,0,30
		ctx.r11.u64 = __builtin_rotateleft64(var_r31 | (var_r31 << 32), 1) & 0xFFFFFFFE;
		// add r10,r11,r26
		ctx.r10.u64 = ctx.r11.u64 + var_r26;
		// lwz r29,0(r25)
		var_r29 = (uint32_t)(PPC_LOAD_U32(var_r25 + 0));
		// lhz r9,-2(r10)
		ctx.r9.u64 = PPC_LOAD_U16(ctx.r10.u32 + -2);
		// lwz r7,16(r29)
		ctx.r7.u64 = PPC_LOAD_U32(var_r29 + 16);
		// mr r8,r9
		ctx.r8.u64 = ctx.r9.u64;
		// lhz r11,0(r7)
		ctx.r11.u64 = PPC_LOAD_U16(ctx.r7.u32 + 0);
		// mr r6,r11
		ctx.r6.u64 = ctx.r11.u64;
		// cmplw cr6,r6,r8
		// beq cr6,0x82135018
		if (ctx.r6.u32 != ctx.r8.u32) {
			// addi r8,r31,1
			ctx.r8.s64 = (int64_t)(int32_t)var_r31 + 1;
			// sth r9,0(r10)
			PPC_STORE_U16(ctx.r10.u32 + 0, ctx.r9.u16);
			// rlwinm r5,r8,1,0,30
			ctx.r5.u64 = __builtin_rotateleft64(ctx.r8.u32 | (ctx.r8.u64 << 32), 1) & 0xFFFFFFFE;
			// addi r31,r8,1
			var_r31 = (uint32_t)(ctx.r8.s64 + 1);  // addr:0x82080001
			// sthx r11,r5,r26
			PPC_STORE_U16(ctx.r5.u32 + var_r26, ctx.r11.u16);
		}
	loc_82135018:
		// not r4,r31
		ctx.r4.u64 = ~var_r31;
		// lwz r3,0(r29)
		ctx.r3.u64 = PPC_LOAD_U32(var_r29 + 0);
		// clrlwi r10,r4,31
		ctx.r10.u64 = ctx.r4.u32 & 0x1;
		// cmpw cr6,r3,r10
		// beq cr6,0x82135038
		if (ctx.r3.s32 != ctx.r10.s32) {
			// rlwinm r9,r31,1,0,30
			ctx.r9.u64 = __builtin_rotateleft64(var_r31 | (var_r31 << 32), 1) & 0xFFFFFFFE;
			// addi r31,r31,1
			var_r31 = (uint32_t)(var_r31 + 1);
			// sthx r11,r9,r26
			PPC_STORE_U16(ctx.r9.u32 + var_r26, ctx.r11.u16);
		}
	loc_82135038:
		// lwz r8,12(r29)
		ctx.r8.u64 = PPC_LOAD_U32(var_r29 + 12);
		// mr r27,r23
		var_r27 = (uint32_t)(var_r23);
		// cmplwi cr6,r8,0
		// ble cr6,0x82135090
		if (ctx.r8.u32 <= 0) goto loc_82135090;
		// rlwinm r11,r31,1,0,30
		ctx.r11.u64 = __builtin_rotateleft64(var_r31 | (var_r31 << 32), 1) & 0xFFFFFFFE;
		// mr r30,r23
		var_r30 = (uint32_t)(var_r23);
		// add r28,r11,r26
		var_r28 = (uint32_t)(ctx.r11.u64 + var_r26);
	loc_82135054:
		// lwz r7,16(r29)
		ctx.r7.u64 = PPC_LOAD_U32(var_r29 + 16);
		// li r4,1
		ctx.r4.s64 = 1;
		// addi r3,r1,80
		ctx.r3.s64 = ctx.r1.s64 + 80;
		// addi r31,r31,1
		var_r31 = (uint32_t)(var_r31 + 1);
		// lhzx r6,r30,r7
		ctx.r6.u64 = PPC_LOAD_U16(var_r30 + ctx.r7.u32);
		// sth r6,0(r28)
		PPC_STORE_U16(var_r28 + 0, ctx.r6.u16);
		// addi r28,r28,2
		var_r28 = (uint32_t)(var_r28 + 2);
		// lwz r5,16(r29)
		ctx.r5.u64 = PPC_LOAD_U32(var_r29 + 16);
		// lhzx r5,r30,r5
		ctx.r5.u64 = PPC_LOAD_U16(var_r30 + ctx.r5.u32);
		// bl 0x821357b8
		cmOperatorCtor_57B8_w(ctx, base);
		// lwz r4,12(r29)
		ctx.r4.u64 = PPC_LOAD_U32(var_r29 + 12);
		// addi r27,r27,1
		var_r27 = (uint32_t)(var_r27 + 1);
		// addi r30,r30,2
		var_r30 = (uint32_t)(var_r30 + 2);
		// cmplw cr6,r27,r4
		// blt cr6,0x82135054
		if (var_r27 < ctx.r4.u32) goto loc_82135054;
	loc_82135090:
		// mr r4,r25
		ctx.r4.u64 = var_r25;
		// mr r3,r24
		ctx.r3.u64 = var_r24;
		// bl 0x82134350
		pongNetMessageHolder_4350_wrh(ctx, base);
		// lwz r3,4(r24)
		ctx.r3.u64 = PPC_LOAD_U32(var_r24 + 4);
		// cmplwi cr6,r3,0
		// bne cr6,0x82134fcc
}
loc_821350A8:
	// mr r3,r31
	ctx.r3.u64 = var_r31;
	// stw r26,0(r22)
	PPC_STORE_U32(var_r22 + 0, var_r26);
	return;
}

PPC_FUNC_IMPL(cmOperatorCtor_54D0_wrh) {
	PPC_FUNC_PROLOGUE();
	uint32_t var_r31 = 0;
	uint32_t var_r28 = 0;
	uint32_t var_r27 = 0;
	uint32_t var_r30 = 0;
	uint32_t var_r29 = 0;
	uint32_t var_r25 = 0;
	uint32_t var_r26 = 0;
	// mflr r12
	ctx.r12.u64 = ctx.lr;
	// bl 0x8242f88c
	ctx.lr = 0x821354D8;
	__savegprlr_25(ctx, base);
	// lis r9,21845
	ctx.r9.s64 = 1431633920;
	// lwz r11,4(r3)
	ctx.r11.u64 = PPC_LOAD_U32(ctx.r3.u32 + 4);
	// rlwinm r31,r4,1,0,30
	var_r31 = (uint32_t)(__builtin_rotateleft64(ctx.r4.u32 | (ctx.r4.u64 << 32), 1) & 0xFFFFFFFE);
	// lwz r28,0(r3)
	var_r28 = (uint32_t)(PPC_LOAD_U32(ctx.r3.u32 + 0));
	// ori r8,r9,21846
	ctx.r8.u64 = ctx.r9.u64 | 21846;
	// addi r10,r5,1
	ctx.r10.s64 = ctx.r5.s64 + 1;
	// add r31,r4,r31
	var_r31 = (uint32_t)(ctx.r4.u64 + var_r31);
	// mulhw r9,r10,r8
	ctx.r9.s64 = (int64_t(ctx.r10.s32) * int64_t(ctx.r8.s32)) >> 32;
	// rlwinm r7,r4,1,0,30
	ctx.r7.u64 = __builtin_rotateleft64(ctx.r4.u32 | (ctx.r4.u64 << 32), 1) & 0xFFFFFFFE;
	// rlwinm r27,r31,1,0,30
	var_r27 = (uint32_t)(__builtin_rotateleft64(var_r31 | (var_r31 << 32), 1) & 0xFFFFFFFE);
	// rlwinm r31,r9,1,31,31
	var_r31 = (uint32_t)(__builtin_rotateleft64(ctx.r9.u32 | (ctx.r9.u64 << 32), 1) & 0x1);
	// add r7,r4,r7
	ctx.r7.u64 = ctx.r4.u64 + ctx.r7.u64;
	// add r9,r9,r31
	ctx.r9.u64 = ctx.r9.u64 + var_r31;
	// add r31,r7,r5
	var_r31 = (uint32_t)(ctx.r7.u64 + ctx.r5.u64);
	// addi r6,r4,1
	ctx.r6.s64 = ctx.r4.s64 + 1;
	// rlwinm r30,r31,1,0,30
	var_r30 = (uint32_t)(__builtin_rotateleft64(var_r31 | (var_r31 << 32), 1) & 0xFFFFFFFE);
	// add r31,r11,r27
	var_r31 = (uint32_t)(ctx.r11.u64 + var_r27);
	// cmpw cr6,r6,r28
	// addi r31,r31,6
	var_r31 = (uint32_t)(var_r31 + 6);
	// lhzx r29,r30,r11
	var_r29 = (uint32_t)(PPC_LOAD_U16(var_r30 + ctx.r11.u32));
	// rlwinm r30,r9,1,0,30
	var_r30 = (uint32_t)(__builtin_rotateleft64(ctx.r9.u32 | (ctx.r9.u64 << 32), 1) & 0xFFFFFFFE);
	// add r9,r9,r30
	ctx.r9.u64 = ctx.r9.u64 + var_r30;
	// subf r10,r9,r10
	ctx.r10.s64 = ctx.r10.s64 - ctx.r9.s64;
	// add r7,r10,r7
	ctx.r7.u64 = ctx.r10.u64 + ctx.r7.u64;
	// rlwinm r10,r7,1,0,30
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r7.u32 | (ctx.r7.u64 << 32), 1) & 0xFFFFFFFE;
	// lhzx r25,r10,r11
	var_r25 = (uint32_t)(PPC_LOAD_U16(ctx.r10.u32 + ctx.r11.u32));
	// bge cr6,0x82135644
	if (ctx.r6.s32 < (int32_t)var_r28) {
		// lwz r10,12(r3)
		ctx.r10.u64 = PPC_LOAD_U32(ctx.r3.u32 + 12);
		// rlwinm r11,r6,2,0,29
		ctx.r11.u64 = __builtin_rotateleft64(ctx.r6.u32 | (ctx.r6.u64 << 32), 2) & 0xFFFFFFFC;
		// add r26,r11,r10
		var_r26 = (uint32_t)(ctx.r11.u64 + ctx.r10.u64);
	loc_82135550:
		// lwz r9,0(r26)
		ctx.r9.u64 = PPC_LOAD_U32(var_r26 + 0);
		// cmpwi cr6,r9,7
		// beq cr6,0x821355ac
		if (ctx.r9.s32 != 7) {
			// li r9,0
			ctx.r9.s64 = 0;
			// mr r30,r31
			var_r30 = (uint32_t)(var_r31);
		loc_82135564:
			// lhz r7,0(r30)
			ctx.r7.u64 = PPC_LOAD_U16(var_r30 + 0);
			// cmpw cr6,r7,r25
			// bne cr6,0x8213559c
			if (ctx.r7.s32 == (int32_t)var_r25) {
				// addi r11,r9,1
				ctx.r11.s64 = ctx.r9.s64 + 1;
				// mulhw r10,r11,r8
				ctx.r10.s64 = (int64_t(ctx.r11.s32) * int64_t(ctx.r8.s32)) >> 32;
				// rlwinm r7,r10,1,31,31
				ctx.r7.u64 = __builtin_rotateleft64(ctx.r10.u32 | (ctx.r10.u64 << 32), 1) & 0x1;
				// add r10,r10,r7
				ctx.r10.u64 = ctx.r10.u64 + ctx.r7.u64;
				// rlwinm r7,r10,1,0,30
				ctx.r7.u64 = __builtin_rotateleft64(ctx.r10.u32 | (ctx.r10.u64 << 32), 1) & 0xFFFFFFFE;
				// add r10,r10,r7
				ctx.r10.u64 = ctx.r10.u64 + ctx.r7.u64;
				// subf r7,r10,r11
				ctx.r7.s64 = ctx.r11.s64 - ctx.r10.s64;
				// rlwinm r11,r7,1,0,30
				ctx.r11.u64 = __builtin_rotateleft64(ctx.r7.u32 | (ctx.r7.u64 << 32), 1) & 0xFFFFFFFE;
				// lhzx r10,r11,r31
				ctx.r10.u64 = PPC_LOAD_U16(ctx.r11.u32 + var_r31);
				// cmpw cr6,r10,r29
				// beq cr6,0x821355c4
				if (ctx.r10.s32 == (int32_t)var_r29) goto loc_821355C4;
			}
		loc_8213559C:
			// addi r9,r9,1
			ctx.r9.s64 = ctx.r9.s64 + 1;
			// addi r30,r30,2
			var_r30 = (uint32_t)(var_r30 + 2);
			// cmpwi cr6,r9,3
			// blt cr6,0x82135564
			if (ctx.r9.s32 < 3) goto loc_82135564;
		}
	loc_821355AC:
		// addi r6,r6,1
		ctx.r6.s64 = ctx.r6.s64 + 1;
		// addi r26,r26,4
		var_r26 = (uint32_t)(var_r26 + 4);
		// addi r31,r31,6
		var_r31 = (uint32_t)(var_r31 + 6);
		// cmpw cr6,r6,r28
		// blt cr6,0x82135550
		if (ctx.r6.s32 < (int32_t)var_r28) goto loc_82135550;
		// b 0x8242f8dc
		__restgprlr_25(ctx, base);
		return;
	loc_821355C4:
		// li r7,1
		ctx.r7.s64 = 1;
		// lwz r30,8(r3)
		var_r30 = (uint32_t)(PPC_LOAD_U32(ctx.r3.u32 + 8));
		// add r11,r27,r5
		ctx.r11.u64 = var_r27 + ctx.r5.u64;
		// rlwinm r10,r6,2,0,29
		ctx.r10.u64 = __builtin_rotateleft64(ctx.r6.u32 | (ctx.r6.u64 << 32), 2) & 0xFFFFFFFC;
		// rlwinm r29,r11,2,0,29
		var_r29 = (uint32_t)(__builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 2) & 0xFFFFFFFC);
		// addi r11,r11,3
		ctx.r11.s64 = ctx.r11.s64 + 3;
		// rlwinm r8,r4,2,0,29
		ctx.r8.u64 = __builtin_rotateleft64(ctx.r4.u32 | (ctx.r4.u64 << 32), 2) & 0xFFFFFFFC;
		// rlwinm r28,r11,2,0,29
		var_r28 = (uint32_t)(__builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 2) & 0xFFFFFFFC);
		// rlwinm r11,r6,1,0,30
		ctx.r11.u64 = __builtin_rotateleft64(ctx.r6.u32 | (ctx.r6.u64 << 32), 1) & 0xFFFFFFFE;
		// stwx r6,r29,r30
		PPC_STORE_U32(var_r29 + var_r30, ctx.r6.u32);
		// lwz r30,8(r3)
		var_r30 = (uint32_t)(PPC_LOAD_U32(ctx.r3.u32 + 8));
		// add r6,r6,r11
		ctx.r6.u64 = ctx.r6.u64 + ctx.r11.u64;
		// rlwinm r11,r6,1,0,30
		ctx.r11.u64 = __builtin_rotateleft64(ctx.r6.u32 | (ctx.r6.u64 << 32), 1) & 0xFFFFFFFE;
		// add r11,r11,r9
		ctx.r11.u64 = ctx.r11.u64 + ctx.r9.u64;
		// stwx r9,r28,r30
		PPC_STORE_U32(var_r28 + var_r30, ctx.r9.u32);
		// rlwinm r6,r11,2,0,29
		ctx.r6.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 2) & 0xFFFFFFFC;
		// addi r11,r11,3
		ctx.r11.s64 = ctx.r11.s64 + 3;
		// slw r31,r7,r5
		var_r31 = (uint32_t)(ctx.r5.u8 & 0x20 ? 0 : (ctx.r7.u32 << (ctx.r5.u8 & 0x3F)));
		// slw r7,r7,r9
		ctx.r7.u64 = ctx.r9.u8 & 0x20 ? 0 : (ctx.r7.u32 << (ctx.r9.u8 & 0x3F));
		// lwz r9,12(r3)
		ctx.r9.u64 = PPC_LOAD_U32(ctx.r3.u32 + 12);
		// rlwinm r11,r11,2,0,29
		ctx.r11.u64 = __builtin_rotateleft64(ctx.r11.u32 | (ctx.r11.u64 << 32), 2) & 0xFFFFFFFC;
		// lwzx r30,r8,r9
		var_r30 = (uint32_t)(PPC_LOAD_U32(ctx.r8.u32 + ctx.r9.u32));
		// or r31,r31,r30
		var_r31 = (uint32_t)(var_r31 | var_r30);
		// stwx r31,r8,r9
		PPC_STORE_U32(ctx.r8.u32 + ctx.r9.u32, var_r31);
		// lwz r9,8(r3)
		ctx.r9.u64 = PPC_LOAD_U32(ctx.r3.u32 + 8);
		// stwx r4,r6,r9
		PPC_STORE_U32(ctx.r6.u32 + ctx.r9.u32, ctx.r4.u32);
		// lwz r8,8(r3)
		ctx.r8.u64 = PPC_LOAD_U32(ctx.r3.u32 + 8);
		// stwx r5,r11,r8
		PPC_STORE_U32(ctx.r11.u32 + ctx.r8.u32, ctx.r5.u32);
		// lwz r11,12(r3)
		ctx.r11.u64 = PPC_LOAD_U32(ctx.r3.u32 + 12);
		// lwzx r6,r10,r11
		ctx.r6.u64 = PPC_LOAD_U32(ctx.r10.u32 + ctx.r11.u32);
		// or r5,r7,r6
		ctx.r5.u64 = ctx.r7.u64 | ctx.r6.u64;
		// stwx r5,r10,r11
		PPC_STORE_U32(ctx.r10.u32 + ctx.r11.u32, ctx.r5.u32);
	}
loc_82135644:
	// b 0x8242f8dc
	__restgprlr_25(ctx, base);
	return;
}

PPC_FUNC_IMPL(cmOperatorCtor_5648_w) {
	PPC_FUNC_PROLOGUE();
	uint32_t var_r26 = 0;
	uint32_t var_r31 = 0;
	uint32_t var_r28 = 0;
	uint32_t var_r27 = 0;
	uint32_t var_r29 = 0;
	uint32_t var_r30 = 0;
	// FRAME: size=144, savegprlr_26
	// mr r26,r4
	var_r26 = ctx.r4.u32;
	// mr r31,r3
	var_r31 = ctx.r3.u32;
	// lis r11,16383
	ctx.r11.s64 = 1073676288;
	// li r28,-1
	var_r28 = (uint32_t)(-1);
	// ori r10,r11,65535
	ctx.r10.u64 = ctx.r11.u64 | 65535;
	// rlwinm r27,r26,2,0,29
	var_r27 = (uint32_t)(__builtin_rotateleft64(var_r26 | (var_r26 << 32), 2) & 0xFFFFFFFC);
	// cmplw cr6,r26,r10
	// stw r26,0(r31)
	PPC_STORE_U32(var_r31 + 0, var_r26);
	// stw r5,4(r31)
	PPC_STORE_U32(var_r31 + 4, ctx.r5.u32);
	// ble cr6,0x82135680
	if (var_r26 > ctx.r10.u32) {
		// mr r27,r28
		var_r27 = (uint32_t)(var_r28);
	}
loc_82135680:
	// bl 0x820c0038
	xe_main_thread_init_0038(ctx, base);
	// lwz r29,0(r13)
	var_r29 = (uint32_t)(PPC_LOAD_U32(ctx.r13.u32 + 0)  /* SDA:0x82600000 */);
	// li r30,4
	var_r30 = 4;
	// li r5,16
	ctx.r5.s64 = 16;
	// mr r4,r27
	ctx.r4.u64 = var_r27;
	// lwzx r3,r30,r29
	ctx.r3.u64 = PPC_LOAD_U32(var_r30 + var_r29);
	// lwz r8,4(r9)
	// bctrl
	VCALL(ctx.r3.u32, 1, ctx, base);  // vtable slot 1 (byte +4)
	// lis r7,2730
	ctx.r7.s64 = 178913280;
	// stw r3,12(r31)
	PPC_STORE_U32(var_r31 + 12, ctx.r3.u32);
	// ori r6,r7,43690
	ctx.r6.u64 = ctx.r7.u64 | 43690;
	// cmplw cr6,r26,r6
	// bgt cr6,0x821356c8
	if (var_r26 <= ctx.r6.u32) {
		// rlwinm r11,r26,1,0,30
		ctx.r11.u64 = __builtin_rotateleft64(var_r26 | (var_r26 << 32), 1) & 0xFFFFFFFE;
		// add r5,r26,r11
		ctx.r5.u64 = var_r26 + ctx.r11.u64;
		// rlwinm r28,r5,3,0,28
		var_r28 = (uint32_t)(__builtin_rotateleft64(ctx.r5.u32 | (ctx.r5.u64 << 32), 3) & 0xFFFFFFF8);
	}
loc_821356C8:
	// bl 0x820c0038
	xe_main_thread_init_0038(ctx, base);
	// lwzx r3,r30,r29
	ctx.r3.u64 = PPC_LOAD_U32(var_r30 + var_r29);
	// li r5,16
	ctx.r5.s64 = 16;
	// mr r4,r28
	ctx.r4.u64 = var_r28;
	// lwz r10,4(r11)
	// bctrl
	VCALL(ctx.r3.u32, 1, ctx, base);  // vtable slot 1 (byte +4)
	// cmpwi cr6,r26,0
	// stw r3,8(r31)
	PPC_STORE_U32(var_r31 + 8, ctx.r3.u32);
	// ble cr6,0x82135730
	if ((int32_t)var_r26 > 0) {
		// li r11,0
		ctx.r11.s64 = 0;
		// mr r10,r26
		ctx.r10.u64 = var_r26;
		// li r9,-1
		ctx.r9.s64 = -1;  // HARNESS: recomp dropped this
	loc_82135700:
		// lwz r8,8(r31)
		ctx.r8.u64 = PPC_LOAD_U32(var_r31 + 8);
		// addi r10,r10,-1
		ctx.r10.s64 = ctx.r10.s64 + -1;
		// cmplwi cr6,r10,0
		// stwx r9,r8,r11
		PPC_STORE_U32(ctx.r8.u32 + ctx.r11.u32, ctx.r9.u32);
		// lwz r8,8(r31)
		ctx.r8.u64 = PPC_LOAD_U32(var_r31 + 8);
		// add r7,r8,r11
		ctx.r7.u64 = ctx.r8.u64 + ctx.r11.u64;
		// stw r9,4(r7)
		PPC_STORE_U32(ctx.r7.u32 + 4, ctx.r9.u32);
		// lwz r8,8(r31)
		ctx.r8.u64 = PPC_LOAD_U32(var_r31 + 8);
		// add r6,r8,r11
		ctx.r6.u64 = ctx.r8.u64 + ctx.r11.u64;
		// addi r11,r11,24
		ctx.r11.s64 = ctx.r11.s64 + 24;
		// stw r9,8(r6)
		PPC_STORE_U32(ctx.r6.u32 + 8, ctx.r9.u32);
		// bne cr6,0x82135700
		if (ctx.r10.u32 != 0) goto loc_82135700;
	}
loc_82135730:
	// lwz r5,0(r31)
	ctx.r5.u64 = PPC_LOAD_U32(var_r31 + 0);
	// li r4,0
	ctx.r4.s64 = 0;
	// lwz r3,12(r31)
	ctx.r3.u64 = PPC_LOAD_U32(var_r31 + 12);
	// rlwinm r5,r5,2,0,29
	ctx.r5.u64 = __builtin_rotateleft64(ctx.r5.u32 | (ctx.r5.u64 << 32), 2) & 0xFFFFFFFC;
	// bl 0x8242fed0
	memset(ctx, base);
	// li r4,0
	ctx.r4.s64 = 0;
	// cmpwi cr6,r26,0
	// ble cr6,0x82135798
	if ((int32_t)var_r26 > 0) {
		// li r28,1
		var_r28 = 1;
	loc_82135754:
		// li r30,0
		var_r30 = 0;
		// rlwinm r29,r4,2,0,29
		var_r29 = (uint32_t)(__builtin_rotateleft64(ctx.r4.u32 | (ctx.r4.u64 << 32), 2) & 0xFFFFFFFC);
	loc_8213575C:
		// lwz r3,12(r31)
		ctx.r3.u64 = PPC_LOAD_U32(var_r31 + 12);
		// slw r10,r28,r30
		ctx.r10.u64 = (uint8_t)var_r30 & 0x20 ? 0 : (var_r28 << ((uint8_t)var_r30 & 0x3F));
		// lwzx r11,r3,r29
		ctx.r11.u64 = PPC_LOAD_U32(ctx.r3.u32 + var_r29);
		// and r9,r11,r10
		ctx.r9.u64 = ctx.r11.u64 & ctx.r10.u64;
		// cmpwi cr6,r9,0
		// bne cr6,0x82135780
		if (ctx.r9.s32 == 0) {
			// mr r5,r30
			ctx.r5.u64 = var_r30;
			// mr r3,r31
			ctx.r3.u64 = var_r31;
			// bl 0x821354d0
			cmOperatorCtor_54D0_wrh(ctx, base);
		}
	loc_82135780:
		// addi r30,r30,1
		var_r30 = (uint32_t)(var_r30 + 1);
		// cmpwi cr6,r30,3
		// blt cr6,0x8213575c
		if ((int32_t)var_r30 < 3) goto loc_8213575C;
		// addi r4,r4,1
		ctx.r4.s64 = ctx.r4.s64 + 1;
		// cmpw cr6,r4,r26
		// blt cr6,0x82135754
		if (ctx.r4.s32 < (int32_t)var_r26) goto loc_82135754;
	}
loc_82135798:
	// lwz r8,0(r31)
	ctx.r8.u64 = PPC_LOAD_U32(var_r31 + 0);
	// li r4,0
	ctx.r4.s64 = 0;
	// lwz r3,12(r31)
	ctx.r3.u64 = PPC_LOAD_U32(var_r31 + 12);
	// rlwinm r5,r8,2,0,29
	ctx.r5.u64 = __builtin_rotateleft64(ctx.r8.u32 | (ctx.r8.u64 << 32), 2) & 0xFFFFFFFC;
	// bl 0x8242fed0
	memset(ctx, base);
	// mr r3,r31
	ctx.r3.u64 = var_r31;
	return;
}

PPC_FUNC_IMPL(cmOperatorCtor_57B8_w) {
	PPC_FUNC_PROLOGUE();
	// mr r11,r3
	ctx.r11.u64 = ctx.r3.u64;
	// li r10,0
	ctx.r10.s64 = 0;
	// addi r9,r11,4
	ctx.r9.s64 = ctx.r11.s64 + 4;
loc_821357C4:
	// lhz r8,0(r9)
	ctx.r8.u64 = PPC_LOAD_U16(ctx.r9.u32 + 0);
	// cmpw cr6,r5,r8
	// beq cr6,0x82135880
	if (ctx.r5.s32 == ctx.r8.s32) goto loc_82135880;
	// addi r10,r10,1
	ctx.r10.s64 = ctx.r10.s64 + 1;
	// addi r9,r9,2
	ctx.r9.s64 = ctx.r9.s64 + 2;
	// cmpwi cr6,r10,18
	// blt cr6,0x821357c4
	if (ctx.r10.s32 < 18) goto loc_821357C4;
	// lwz r9,112(r11)
	ctx.r9.u64 = PPC_LOAD_U32(ctx.r11.u32 + 112);
	// li r3,1
	ctx.r3.s64 = 1;
	// addi r8,r9,2
	ctx.r8.s64 = ctx.r9.s64 + 2;
	// rlwinm r10,r8,1,0,30
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r8.u32 | (ctx.r8.u64 << 32), 1) & 0xFFFFFFFE;
	// lhzx r7,r10,r11
	ctx.r7.u64 = PPC_LOAD_U16(ctx.r10.u32 + ctx.r11.u32);
	// cmplwi cr6,r7,65535
	// beq cr6,0x82135824
	if (ctx.r7.u32 != 65535) {
		// addi r6,r9,10
		ctx.r6.s64 = ctx.r9.s64 + 10;
		// rlwinm r8,r6,2,0,29
		ctx.r8.u64 = __builtin_rotateleft64(ctx.r6.u32 | (ctx.r6.u64 << 32), 2) & 0xFFFFFFFC;
		// lwzx r7,r8,r11
		ctx.r7.u64 = PPC_LOAD_U32(ctx.r8.u32 + ctx.r11.u32);
		// cmpw cr6,r7,r4
		// bne cr6,0x82135824
		if (ctx.r7.s32 != ctx.r4.s32) goto loc_82135824;
		// add r6,r9,r11
		ctx.r6.u64 = ctx.r9.u64 + ctx.r11.u64;
		// lbz r9,116(r6)
		ctx.r9.u64 = PPC_LOAD_U8(ctx.r6.u32 + 116);
		// cmplwi cr6,r9,0
		// bne cr6,0x82135824
		if (ctx.r9.u32 != 0) goto loc_82135824;
		// li r3,2
		ctx.r3.s64 = 2;
	}
loc_82135824:
	// sthx r5,r10,r11
	PPC_STORE_U16(ctx.r10.u32 + ctx.r11.u32, ctx.r5.u16);
	// li r8,0
	ctx.r8.s64 = 0;
	// lwz r10,112(r11)
	ctx.r10.u64 = PPC_LOAD_U32(ctx.r11.u32 + 112);
	// lis r7,14563
	ctx.r7.s64 = 954400768;
	// addi r5,r10,10
	ctx.r5.s64 = ctx.r10.s64 + 10;
	// ori r6,r7,36409
	ctx.r6.u64 = ctx.r7.u64 | 36409;
	// rlwinm r10,r5,2,0,29
	ctx.r10.u64 = __builtin_rotateleft64(ctx.r5.u32 | (ctx.r5.u64 << 32), 2) & 0xFFFFFFFC;
	// stwx r4,r10,r11
	PPC_STORE_U32(ctx.r10.u32 + ctx.r11.u32, ctx.r4.u32);
	// lwz r10,112(r11)
	ctx.r10.u64 = PPC_LOAD_U32(ctx.r11.u32 + 112);
	// add r9,r10,r11
	ctx.r9.u64 = ctx.r10.u64 + ctx.r11.u64;
	// stb r8,116(r9)
	PPC_STORE_U8(ctx.r9.u32 + 116, ctx.r8.u8);
	// lwz r10,112(r11)
	ctx.r10.u64 = PPC_LOAD_U32(ctx.r11.u32 + 112);
	// addi r10,r10,1
	ctx.r10.s64 = ctx.r10.s64 + 1;
	// mulhw r7,r10,r6
	ctx.r7.s64 = (int64_t(ctx.r10.s32) * int64_t(ctx.r6.s32)) >> 32;
	// srawi r9,r7,2
	ctx.xer.ca = (ctx.r7.s32 < 0) & ((ctx.r7.u32 & 0x3) != 0);
	ctx.r9.s64 = ctx.r7.s32 >> 2;
	// rlwinm r8,r9,1,31,31
	ctx.r8.u64 = __builtin_rotateleft64(ctx.r9.u32 | (ctx.r9.u64 << 32), 1) & 0x1;
	// add r9,r9,r8
	ctx.r9.u64 = ctx.r9.u64 + ctx.r8.u64;
	// rlwinm r8,r9,3,0,28
	ctx.r8.u64 = __builtin_rotateleft64(ctx.r9.u32 | (ctx.r9.u64 << 32), 3) & 0xFFFFFFF8;
	// add r6,r9,r8
	ctx.r6.u64 = ctx.r9.u64 + ctx.r8.u64;
	// rlwinm r5,r6,1,0,30
	ctx.r5.u64 = __builtin_rotateleft64(ctx.r6.u32 | (ctx.r6.u64 << 32), 1) & 0xFFFFFFFE;
	// subf r4,r5,r10
	ctx.r4.s64 = ctx.r10.s64 - ctx.r5.s64;
	// stw r4,112(r11)
	PPC_STORE_U32(ctx.r11.u32 + 112, ctx.r4.u32);
	// blr
	return;
loc_82135880:
	// addi r7,r10,10
	ctx.r7.s64 = ctx.r10.s64 + 10;
	// rlwinm r9,r7,2,0,29
	ctx.r9.u64 = __builtin_rotateleft64(ctx.r7.u32 | (ctx.r7.u64 << 32), 2) & 0xFFFFFFFC;
	// lwzx r6,r9,r11
	ctx.r6.u64 = PPC_LOAD_U32(ctx.r9.u32 + ctx.r11.u32);
	// cmpw cr6,r4,r6
	// beq cr6,0x821358b0
	if (ctx.r4.s32 != ctx.r6.s32) {
		// lwz r8,0(r11)
		ctx.r8.u64 = PPC_LOAD_U32(ctx.r11.u32 + 0);
		// add r3,r10,r11
		ctx.r3.u64 = ctx.r10.u64 + ctx.r11.u64;
		// li r10,1
		ctx.r10.s64 = 1;
		// addi r5,r8,1
		ctx.r5.s64 = ctx.r8.s64 + 1;
		// stw r5,0(r11)
		PPC_STORE_U32(ctx.r11.u32 + 0, ctx.r5.u32);
		// stwx r4,r9,r11
		PPC_STORE_U32(ctx.r9.u32 + ctx.r11.u32, ctx.r4.u32);
		// stb r10,116(r3)
		PPC_STORE_U8(ctx.r3.u32 + 116, ctx.r10.u8);
	}
loc_821358B0:
	// li r3,0
	ctx.r3.s64 = 0;
	// blr
	return;
}

