Retrospective date note (added October 8, 2026): Existing entries are preserved. Missing milestones below were reconstructed from the conversation, repository documentation, commit history, and dated test output. Entries explicitly identified as commit records indicate when work was committed, not necessarily when every change was written. Work without reliable daily timestamps is grouped into a date range rather than assigned an invented date.

# Jun 30, 2026

Wrote the python script for golden reference model.

## Decisions made
- **Operand format:** Q1.7 (8-bit signed, 7 fractional bits). Range: [-1.0, +127/128].
- **Product format:** Q2.14 (16-bit). Fractional bits add (7+7=14), and the total amount of bits double (8+8=16). Full 16 bits required because of two's complement asymmetry: (-128) x (-128) = +16384, which exceeds the 15-bit signed maximum of +16383.
- **Accumulator:** 32-bit signed. Overflow occurs at $N \approx 2^{17}$ products. Since this is over the 32-bit accumulator, overflow is practically eliminated.
- **Rounding:** Round-to-nearest over truncation. Since truncation produces systemic bias, round-to-nearest was selected to distribute error so they more or less cancel out one another.
- **Saturation:** Clamp to $[-2^{31}, 2^{31}-1]$ without any wrapping. Wrapping is not preferred to eliminate sign flip errors in ML inference process.

## Verification - Test Cases and Results

**Case 1**:

$$A = \begin{bmatrix} 64 \end{bmatrix}, \quad B = \begin{bmatrix} 64 \end{bmatrix}$$

$$C_{fixed} = \begin{bmatrix} 4096 \end{bmatrix}, \quad C_{float} = \begin{bmatrix} 0.25 \end{bmatrix}$$

**Case 2**:

$$A = \begin{bmatrix} -128 \end{bmatrix}, \quad B = \begin{bmatrix} -128 \end{bmatrix}$$

$$C_{fixed} = \begin{bmatrix} 16384 \end{bmatrix}, \quad C_{float} = \begin{bmatrix} 1.0 \end{bmatrix}$$

**Case 3**:

$$A = \begin{bmatrix} 64 & -128 \\ 127 & 32 \end{bmatrix}, \quad B = \begin{bmatrix} 64 & -64 \\ 127 & 32 \end{bmatrix}$$

$$C_{fixed} = \begin{bmatrix} -12160 & -8192 \\ 12192 & -7104 \end{bmatrix}, \quad C_{float} = \begin{bmatrix} -0.7422 & -0.5 \\ 0.7441 & -0.4336 \end{bmatrix}$$

# Jul 1, 2026

## Commit record

- Committed the golden reference model and initial log in `f19d194`. The original implementation notes remain under June 30 above.

# Jul 4, 2026

## Commit records

- Implemented an adder and checked the cocotb/Icarus simulation harness (`1f4b7ce`).
- Implemented and verified the multiply-accumulate processing element (`ad8d83b`).
- These dates come from commit history; detailed daily test output was not retained in this log.

# Jul 10, 2026

## Commit records

- Added and tested the PE pass-through ports needed for systolic dataflow (`c517c83`).
- Connected the processing elements into a 2×2 systolic array and verified its outputs against the golden reference model (`a4520c0`).

# Sep 20, 2026

- Fixed PE saturation by adding a 33-bit intermediary variable to detect overflows before storing the sum in a 32-bit output register.
- Expanded the PE tests for
  - Positive and negative saturation cases
  - Overflow from positive maximum and negative minimum values
- Fixed the golden model scripts by using native Python integers in intermediate arithmetic operations and clamped the intermediary sum after each addition to prevent possible overflow before clipping.
- Improved numerical behavior by having outputs retain 14 fractional bits without any rounding.
- Connected the array test script to the golden reference models, and confirmed that
  - Expected outputs are computed automatically
  - Hardware inputs come from the same matrices
- Created a reusable matrix-test helper function that resets, drives, and checks each matrix multiplication.
- Added matrix multiplication test cases for
  - Mixed signs, positive operands, zero matrix multiplied by a nonzero matrix, minimum valued operands, mixed extreme values, and matrices with cancelling operations.
- Added a configurable randomized testing that allows the control of seed and case count. Additionally, the testing script, if happens, identifies inputs, case type, and output mismatch in case of failure.
- Tested pausing mechanism where the accumulators hold during two disabled clock edges after Cycle 0, and computation resumes correctly.
- Tested 10,000 random matrices passed for each of seeds 42 and 123, both before and after adding the pause, totaling 20,000 random cases per execution mode, with directed checks.

To run the array regression, execute these commands from `tb/` with the virtual environment active:

```sh
PYTHONPATH=.. TEST_SEED=42 NUM_CASES=10000 make
PYTHONPATH=.. TEST_SEED=123 NUM_CASES=10000 make
```

# Sep 21-22, 2026

## Array control verification

- Made stalls optional and extracted the accumulator-hold checks into `pause_array`.
- Ran each random matrix pair uninterrupted and with a two-cycle stall after Cycle 0 on seeds `42` and `123`, and each passed 7 directed cases and 20,000 random executions (10,000 matrix pairs per seed).
- Expanded the regression to stall after Cycle 0, 1, or 2, for 1, 2, or 5 clock cycles. Each matrix pair now runs ten times: once uninterrupted and once for each of the nine stall combinations.
- The expanded regression passed 7 directed cases and 1,000 random executions with seed `42` (100 matrix pairs). Hold assertions check all four accumulators during each disabled edge, and the final outputs are compared against the golden model.
- Added a separate reset-interruption test. It starts a multiplication, confirms nonzero output, asserts asynchronous reset after Cycle 0, and checks that outputs clear before the next rising edge. A fresh multiplication using different matrices then passes without an additional reset.
- Added `reset_before` to the matrix helper so the recovery test can avoid masking a reset problem with a second reset.

## Golden-model regression

- Added standalone `unittest` tests for all three hand-verified arithmetic cases, using hard-coded expected results.
- Added positive and negative accumulator saturation tests using long dot products.
- Added recovery tests that reach each saturation limit and then add an opposite-sign product. These verify that saturation occurs after each addition and that the accumulator can move away from either limit.
- Moved input arrays into their respective test methods to avoid shared mutable test data and simplify naming.
- All seven golden-model tests pass.

## Test commands

From the repository root, with the virtual environment active:

```sh
python -m unittest discover -s model -p 'test_*.py'
```

From `tb/`, run the expanded array regression and reset-interruption test:

```sh
PYTHONPATH=.. TEST_SEED=42 NUM_CASES=100 make
```

# Sep 27, 2026

## Numerical analysis and recorded verification

- Committed the expanded array stall/reset tests and golden-model regressions (`03d6c99`). The earlier September 21–22 entry describes their development.
- The numerical-analysis documentation records results reproduced on September 27: 1,000 random matrix pairs per amplitude, using amplitudes 0.25, 0.5, 1.0, and 1.5 with seed 42.
- Measured mean and maximum absolute error, normalized RMSE, and input clipping. Distinguished input quantization error from RTL correctness and accumulator saturation.
- Among those settings, amplitude 1.0 had the lowest normalized RMSE, while amplitude 0.25 had the lowest absolute error. Heavy clipping at amplitude 1.5 substantially increased error; no universal optimal amplitude was established.
- Documented the experiment and reproduction commands in `model/README.md`.

# Sep 28, 2026

## Controller milestone — commit record

- Committed the accelerator controller, its tests, numerical-analysis script, and supporting documentation (`f19e325`).
- Added IDLE, CLEAR, four computation steps, and DONE sequencing. Accepted requests capture both packed operands; requests while busy are ignored, and done remains asserted until restart or reset.
- Verified operand capture, busy-start rejection, result hold, restart without external reset, reset interruption/recovery, and randomized consecutive operations.
- The controller documentation records passing 10,000 random operations for each of seeds 42 and 123, in addition to directed checks. This records the milestone's documented evidence rather than assigning every individual test run to the commit date.

# Sep 28–Oct 5, 2026 — integration work, exact daily dates unavailable

- Added the register wrapper with CONTROL, STATUS, packed A/B operands, and four read-only result registers.
- Implemented byte-write strobes, ignored writes to read-only/unmapped registers, operand preparation while busy, and reset behavior.
- Added the full-address bus adapter and accelerator top level, mapping the accelerator to `0x40000000`–`0x400000FF`.
- Added the PicoRV32 native-memory interface wrapper and a 4 KiB byte-write-enabled RAM at `0x00000000`–`0x00000FFF`.
- Connected RAM and accelerator through `memory_system`; unmapped requests receive no acknowledgement.
- Added the vendored PicoRV32 core and license and connected it in `soc_top`, including active-low CPU reset conversion, reset address zero, and initial stack address `0x1000`.
- Added component tests for the wrapper, address adapter, accelerator top, CPU-facing interface, RAM, and shared memory system.
- Added optional RAM initialization through `INIT_FILE` and passed the parameter through the SoC hierarchy.

# Oct 5, 2026

## CPU boot and firmware integration

- Corrected the RAM declaration order so `$readmemh` could initialize the declared memory when an image was supplied.
- Ran the three-instruction boot image on PicoRV32: loaded 42, stored it at RAM address `0x100`, then entered a halt loop. Verified both the accepted write and committed RAM contents, followed by 20 cycles without a trap.
- Installed and verified the RISC-V GCC/binutils toolchain after the local Apple Clang failed to assemble the RV32I program.
- Wrote assembly firmware to write the accelerator A register, read it back, and store the readback in RAM.
- Wrote matrix firmware that loads A/B, starts the accelerator, polls done, and stores all four results. First checked equal positive operands, then distinct signed inputs against the golden model.
- Added a second multiplication without reset, using zero A and unchanged B. Verified all 13 expected writes and eight stored result words; the SoC test passed at 2041 ns.

## Build automation, regression, and setup

- Added firmware assembly-to-ELF and ELF-to-hex Make rules, preserving 32-bit RAM word ordering.
- Added `make -C tb test-soc` and root `make test`, with the project root exported on `PYTHONPATH`.
- Ran the complete regression: seven golden-model tests and 14 cocotb tests across ten RTL suites passed.
- Added pinned Python requirements, setup/test instructions, and updated the SoC/register-map documentation.
- Added ignore rules for generated ELF, simulator outputs, and generated matrix/benchmark hex files.
- Added a GitHub Actions workflow to install tools and run regression, then extended it to run benchmarks. Workflow syntax was checked locally; a hosted run remained pending a commit and push.

## Initial cycle comparison

- Created accelerator and software benchmark firmware with common RAM inputs at `0x600`/`0x604`, outputs at `0x700`–`0x70C`, and timing markers at `0x7F0`/`0x7F4`.
- Implemented signed shift-and-add multiplication for the CPU configuration without a hardware multiplier.
- Added a cocotb case runner that initializes RAM while reset is asserted, measures cycles between accepted marker writes, and checks output RAM against the golden model.
- Added four directed cases and 20 random matrix pairs using NumPy seed 42. Both implementations passed all 24 cases.
- Added individual benchmark targets and root `make benchmark`, running implementations sequentially.

| Case | Accelerator cycles | Shift-and-add cycles |
|---|---:|---:|
| Mixed signs | 100 | 1653 |
| Zero multipliers | 100 | 329 |
| Minimum multipliers (`-128`) | 100 | 1905 |
| Maximum multipliers (`127`) | 100 | 1729 |
| 20 random pairs, seed 42 | 100 | 1227–1723 |

- Documented that timings include operand reads, computation, result stores, accelerator setup/polling, and end-marker overhead, while excluding boot and input initialization.
- Rebuilt regression and benchmark images in a temporary source-only copy. All tests passed and reproduced the documented timings. Validation used the existing installed Python environment and tools, not a fresh dependency installation.

# Oct 8, 2026

## Stronger benchmark verification

- Added a monitor requiring full-word markers with value 1, a single start/end sequence, and exactly one correct write to each result address inside the measured interval.
- Added checks for firmware error markers, duplicate/partial/out-of-order result writes, and post-completion marker/result writes and traps.
- Poisoned output RAM before each case to prevent stale results from satisfying final-value checks.
- Added eight unit tests covering valid operation and rejection of invalid marker/result sequences.

## Hardware-multiply comparison

- Exposed PicoRV32's iterative multiplier through `soc_top.ENABLE_MUL`, leaving it disabled by default. The fast multiplier and divider remain disabled.
- Added an assembly software baseline using eight `mul` instructions and reran the assembly accelerator on the same multiplier-enabled CPU configuration.
- Both variants passed the same 24 matrix cases. The accelerator measured 100 cycles and MUL-based software measured 449 cycles: a 4.49× ratio for these inputs and implementations.

## C firmware

- Added RV32I startup assembly, a linker script, a C accelerator driver, and a C benchmark application.
- Startup initializes the stack, clears BSS, calls `main`, and halts after return. Initialized data is included in the RAM image.
- Reserved separate regions for code, benchmark buffers, C globals, and stack space. Linker memory regions reject oversized code/globals before they can overlap benchmark buffers.
- Implemented volatile MMIO, a busy check, bounded status polling, four result reads, and explicit busy/timeout return codes.
- Tested initialized-data and BSS behavior using a cookie and counter across repeated resets.
- The C accelerator path passed all 24 matrix cases and measured 162 cycles per operation locally with GCC 16.2.0 and `-Os`. Busy/timeout error branches were documented but were not fault-injected in these matrix tests.

## Reports, CI, and documentation

- Added per-variant JSON reports with case inputs, expected results, cycle counts, CPU configuration, compiler/Python/NumPy versions, and firmware-image hashes.
- Added CSV, JSON, and Markdown summaries with per-case ratios and aggregate statistics. Report generation rejects mismatched inputs, CPU configurations, and invalid counts; five unit tests cover report behavior.
- Extended `make benchmark` to run five variants sequentially and regenerate reports, clearing old report files before a new combined run.
- Extended CI to run all benchmarks and upload successful reports. No commit, push, or hosted CI execution was performed.
- Updated the README and added `firmware/README.md` covering the driver, memory layout, startup behavior, measurement boundaries, reproduction commands, and limitations.

## Final clean-source validation

- Rebuilt from a temporary source copy without generated firmware images or simulator outputs, using the existing Python environment and local toolchain.
- Passed 20 Python unit tests: seven model, eight benchmark-monitor, and five report-generator tests.
- Passed all 14 cocotb regression tests across ten RTL suites.
- Passed five benchmark tests, each executing 24 matrix cases: 120 successful case executions.
- Checked workflow YAML/shell syntax and reproduced the documented cycle counts.

| Implementation | CPU multiplier | Cycles across 24 cases |
|---|---|---:|
| Assembly accelerator | Disabled | 100 |
| Shift-and-add software | Disabled | 329–1905 |
| Assembly accelerator | Iterative multiplier enabled | 100 |
| MUL-based software | Iterative multiplier enabled | 449 |
| C accelerator driver | Disabled | 162 |

These are simulation measurements for the supplied implementations and inputs. They do not establish FPGA frequency, resource usage, power consumption, or a general workload speedup. Initialized RAM data is not restored on a warm reset; C startup clears BSS, and the benchmark testbench reloads inputs for each case.

## Reproduction

From the project root:

```sh
source .venv/bin/activate
make test
make benchmark
```

Reports are generated under `build/benchmark/`. Commit/push and confirmation of the first hosted CI run remain pending.
