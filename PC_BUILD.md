# Native PC build via vcos_build (no `-sim 1`)

## Model

| Layer | Value |
| --- | --- |
| Studio / plugins | `PC_Common` + **`vs20xx`** (kept in `.vcosproject`) |
| Host compile | **`-compiler gcc`** + NuttX `arch/sim` |
| Board | `pc` → `vendor/ecubus/boards/pc/configs/vcos` |
| MCAL | `vendor/ecubus/components/Can` |
| Board/chip sources | reuses `vendor/semidrive/{boards,chips}/sim` via CUSTOM_DIR |

This is **not** the Infineon/芯驰 `-sim 1` flow. Defconfig already has `CONFIG_ARCH=sim`.

## Prerequisite

- App under `vcos/examples/<app>` with `system_cfg/pc/` and `gen_data/` (Studio/AutoC, `vs20xx`).
- Host tools: `cmake`, `ninja` (or make), host `gcc` (NuttX sim often needs multilib / `gcc-multilib` / `libc6-i386` on Linux).
- Project `.venv` with `kconfiglib` (`pip install kconfiglib` if cmake complains).

Prefer `-gcmake -fc` **without** `-codegen` when `gen_data` already exists.  
If you pass `-codegen` with `-compiler gcc` on board `pc`, vcos_build **does not** overwrite project `compiler` to gcc.

## Command (verified 2026-10-25 Asia/Shanghai)

```bash
cd vcos/build
python vcos_build.py \
  -app_name minimal_system5 \
  -board_name pc \
  -compiler gcc \
  -maketool ninja \
  -update \
  -gcmake -fc
```

**Result:** `# successful generate minimal_system5`  
**Binary:** `vcos/../output/minimal_system5_pc_gcc/minimal_system5`

Same pattern for `minimal_system9` once `system_cfg/pc/gen_data` is ready.

`-gcmake -fc` together is supported (configure then full compile, no codegen).
