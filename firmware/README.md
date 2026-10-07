# Firmware

Build commands run from the project root with the Python virtual environment active for simulations.

| Command | Purpose |
|---|---|
| `make -C firmware` | Build the two-operation assembly regression image |
| `make -C firmware benchmark_c.hex` | Build the C accelerator application |
| `make -C tb benchmark-c` | Test C startup and the driver on 24 input pairs |
| `make benchmark` | Build, test, and compare all five benchmark variants |

The default tools are `riscv64-elf-gcc` and `riscv64-elf-objcopy`. Override `CC` and `OBJCOPY` on the Make command line when the toolchain uses a different prefix. GNU Make propagates those overrides to recursive builds.

## Programs and CPU configuration

| Image | Implementation | CPU hardware multiplier |
|---|---|---|
| `matmul.hex` | Two assembly accelerator operations without reset | Disabled |
| `benchmark_accel.hex` | Assembly accelerator operation | Tested disabled and enabled |
| `benchmark_sw.hex` | Signed shift-and-add products in software | Disabled |
| `benchmark_mul.hex` | Eight `mul` instructions plus additions | Enabled |
| `benchmark_c.hex` | C application calling the accelerator driver | Disabled |

`soc_top.ENABLE_MUL=1` selects PicoRV32's iterative multiplier. The fast multiplier and divider remain disabled. Although the MUL image is assembled with `-march=rv32im`, it only uses multiplication from the M extension; this configuration does not implement division. The other images use RV32I and the ILP32 ABI.

## C startup and memory layout

`start.S` initializes the stack pointer, clears `.bss`, calls `main`, and loops after `main` returns. `link.ld` places code at the CPU's reset address and keeps the benchmark buffers separate from C globals and the stack. Oversized code or globals cause a link error.

| Byte addresses | Use |
|---|---|
| `0x000`–`0x5FF` | Instructions and read-only constants |
| `0x600`, `0x604` | Packed input matrices A and B |
| `0x700`–`0x70F` | Four signed 32-bit results, row-major |
| `0x7F0`, `0x7F4` | Start and end markers, each a full-word write of 1 |
| `0x7F8` | Firmware error code |
| `0x800`–`0xBFF` | C `.data` and `.bss` |
| `0xC00`–`0xFFF` | Reserved stack space, growing down from `0x1000` |

The hex image includes `.text` and initialized `.data`; `$readmemh` loads both into RAM. This RAM-only startup clears `.bss` on each reset but does not restore modified `.data` on a warm reset. No ROM-to-RAM copy, standard C library, heap, or operating system is required. The small application fits within the reserved stack area; there is no runtime stack-overflow guard.

`benchmark_c.c` checks an initialized data cookie and a zero-initialized BSS counter before each run. It sets the counter so the next reset also tests BSS clearing. Startup failures write error code 3 to `0x7F8`.

## Accelerator driver

`accelerator_matmul(a, b, results, poll_limit)` accepts two packed matrices and a writable pointer to four result words. A matrix is packed with elements `[00, 01, 10, 11]` in bytes from least to most significant. Each byte represents a signed Q1.7 value. Results retain 14 fractional bits.

The driver uses volatile register accesses, checks for a busy accelerator, writes both operands and CONTROL, polls STATUS, and reads the four results. Return values are:

| Return | Meaning |
|---|---|
| `0` | Results copied successfully |
| `-1` | Accelerator was busy; no new start requested |
| `-2` | Poll budget exhausted after requesting the operation |

A timeout does not cancel an in-flight hardware operation. The benchmark application uses a budget of 1000 status reads and reports driver failures through `0x7F8`. The success path, signed arithmetic, result order, and repeated startup are tested on the actual simulated SoC. Busy/timeout return paths are not fault-injected by the matrix benchmark.

## Benchmark inputs and measurement

Benchmark programs expect the testbench to populate the input words while reset is asserted. They do not embed specific matrix constants. Cocotb supplies the same four directed and 20 seeded random cases to every variant, resets between cases, and compares results with the Python model. `matmul.S` remains the self-contained two-operation firmware example.

The monitor requires full-word markers with value 1, a single start followed by a single end, and exactly one correct full-word write to each result address between them. It rejects firmware error markers and checks the final RAM contents. Result RAM is poisoned before each case, and a post-completion observation period detects extra marker or result writes and traps.

Cycle counts are the difference between accepted start and end writes. They include operand loads, the operation, result stores, and end-marker overhead. Accelerator paths also include register writes and polling; the C path includes the driver call. Boot, stack/BSS setup, and testbench input initialization are outside the interval. Compiler changes may change the C result.

Reports in `build/benchmark/` include per-case matrices, expected results, cycles, CPU multiplier configuration, compiler/Python/NumPy versions, and a firmware-image SHA-256. `summary.csv`, `summary.json`, and `summary.md` compare matching cases and reject mismatched inputs or CPU configurations. These generated files are ignored by Git and uploaded by CI after successful benchmarks.
