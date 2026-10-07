# Build bare-metal RISC-V firmware and RAM images.

CC = riscv64-elf-gcc
OBJCOPY = riscv64-elf-objcopy
ARCH_FLAGS = -march=rv32i -mabi=ilp32
.DEFAULT_GOAL := matmul.hex
.SECONDARY:
CFLAGS = -march=rv32i -mabi=ilp32 -Os -ffreestanding -fno-builtin -fno-pic -fno-stack-protector -msmall-data-limit=0 -Wall -Wextra -Werror

benchmark_mul.elf: benchmark_mul.S Makefile link.ld
	$(CC) -march=rv32im -mabi=ilp32 -nostdlib -Wl,-T,link.ld -Wl,--no-relax -Wl,--build-id=none $< -o $@

benchmark_c.elf: start.S benchmark_c.c accelerator.c accelerator.h link.ld Makefile
	$(CC) $(CFLAGS) -nostdlib -Wl,-T,link.ld -Wl,--no-relax -Wl,--build-id=none start.S benchmark_c.c accelerator.c -o $@

benchmark_accel.elf: benchmark_accel.S Makefile link.ld
	$(CC) $(ARCH_FLAGS) -nostdlib -Wl,-T,link.ld -Wl,--no-relax -Wl,--build-id=none $< -o $@

benchmark_sw.elf: benchmark_sw.S Makefile link.ld
	$(CC) $(ARCH_FLAGS) -nostdlib -Wl,-T,link.ld -Wl,--no-relax -Wl,--build-id=none $< -o $@

%.elf: %.S Makefile
	$(CC) $(ARCH_FLAGS) -nostdlib -Wl,-Ttext=0x0 -Wl,-e,_start -Wl,--no-relax $< -o $@

%.hex: %.elf Makefile
	$(OBJCOPY) -O verilog --verilog-data-width=4 -j .text -j .data $< $@
