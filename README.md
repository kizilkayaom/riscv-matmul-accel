# riscv-matmul-accel

A fixed-point 2×2 matrix-multiplication accelerator integrated with a PicoRV32 RISC-V core and 4 KiB of RAM through a memory-mapped register interface. Verified in simulation: assembly firmware runs two multiplications without reset, and cocotb checks the results stored in RAM against a Python golden model.

- [Controller interface and verification](rtl/array/README.md)
- [Golden model and numerical error analysis](model/README.md)
- [Firmware, C driver, and benchmark methodology](firmware/README.md)
- [Engineering log](log.md)

## Setup

The regression has been tested with Python 3.13, cocotb 2.0.1, NumPy 2.4.6, Icarus Verilog 13.0, and RISC-V GCC 16.2.0. GNU Make is also required.

On macOS, with Homebrew and the Xcode Command Line Tools installed, install the external tools:

```sh
brew install python@3.13 icarus-verilog riscv64-elf-gcc
```

Package details: [Python 3.13](https://formulae.brew.sh/formula/python@3.13), [Icarus Verilog](https://formulae.brew.sh/formula/icarus-verilog), and [RISC-V GCC](https://formulae.brew.sh/formula/riscv64-elf-gcc). The GCC package also installs RISC-V binutils, including `riscv64-elf-objcopy`.

From the project root, create and activate the Python environment, then install the pinned dependencies:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Keep the virtual environment active when running tests so `python` and `cocotb-config` are available. The firmware build expects `riscv64-elf-gcc` and `riscv64-elf-objcopy` on `PATH`; it selects RV32I with the ILP32 ABI for PicoRV32.

## Running tests

Run these commands from the project root with the project dependencies installed:

```sh
source .venv/bin/activate
make test
```

`make test` runs the Python golden-model, benchmark-monitor, and report-generator unit tests and all 10 RTL test suites, ending with the PicoRV32 SoC test. It rebuilds the SoC firmware when needed before running the simulation.

To run only the CPU integration test, with the virtual environment active:

```sh
make -C tb test-soc
```

This also builds the firmware when needed and checks two successive accelerator operations against the golden model, including the results stored in RAM.

The GitHub Actions workflow runs the regression followed by all five benchmark variants on pushes and pull requests, using Ubuntu 24.04 and Python 3.13. It passes Ubuntu's `riscv64-unknown-elf-gcc` and `riscv64-unknown-elf-objcopy` names to Make. Successful benchmark runs upload the generated reports as a `benchmark-reports` artifact. The first hosted run remains pending until these changes are committed and pushed.

## Benchmark

From the project root, with the virtual environment active:

```sh
make benchmark
```

This builds and runs five variants sequentially, each with the same 24 cases (four directed and 20 random, NumPy seed 42). Every result is checked against the golden model. The CPU and accelerator reset between cases; inputs are loaded into RAM by the testbench.

| Variant | CPU multiplier | Implementation | Cycles across 24 cases |
|---|---|---|---:|
| `accel` | Disabled | Assembly accelerator driver | 100 |
| `sw` | Disabled | Software shift-and-add | 329–1905 |
| `accel_mul` | Iterative multiplier enabled | Same assembly accelerator driver | 100 |
| `mul` | Iterative multiplier enabled | Software using eight `mul` instructions | 449 |
| `c` | Disabled | C accelerator application and driver (`-Os`) | 162 |

These measurements use the tool versions listed above. The hardware-multiply comparison enables the same multiplier for both `accel_mul` and `mul`; the fast multiplier and divider remain disabled. The C image includes startup code, a linker script, and a bounded-polling driver. Its cycle count can change with the compiler.

The original directed inputs are:

```text
A = [[64, -128], [127, 32]]
B = [[64,  -64], [127, 32]]
```

Other directed cases keep A unchanged and fill B with `0`, `-128`, or `127`. Random cases draw both matrices from the full signed-int8 range.

| Case | Assembly accelerator | Shift-and-add software | Software / accelerator |
|---|---:|---:|---:|
| Mixed signs | 100 | 1653 | 16.53× |
| Zero multipliers | 100 | 329 | 3.29× |
| Minimum multipliers (`-128`) | 100 | 1905 | 19.05× |
| Maximum multipliers (`127`) | 100 | 1729 | 17.29× |
| 20 random pairs (range) | 100 | 1227–1723 | 12.27–17.23× |

With hardware multiplication enabled, the software-to-accelerator ratio is **4.49×** for these cases. The C accelerator path takes **1.62×** the cycles of the assembly accelerator path on the multiplier-disabled CPU. These are comparisons of the supplied implementations, not claims about an optimal software baseline.

Timing runs from the accepted full-word start-marker write at `0x7F0` to the end-marker write at `0x7F4`. It includes input reads, computation, result stores, end-marker overhead, and accelerator setup/polling or C call overhead where applicable. Boot, C runtime initialization, and testbench input initialization are excluded. All four correct full-word result writes must occur exactly once inside the interval; the test also checks final RAM and observes post-completion behavior.

Machine-readable and human-readable reports are generated in `build/benchmark/`:

- One JSON file per variant, including inputs, expected results, cycle counts, configuration, tool versions, and firmware hash.
- `summary.csv` and `summary.json` with per-case cycle counts and ratios.
- `summary.md` with statistics and the full comparison table.

Run one variant with `make -C tb benchmark-c`, `benchmark-mul`, `benchmark-accel-mul`, `benchmark-accel`, or `benchmark-sw`. `make benchmark` runs all variants and validates that report inputs and measurement boundaries match before combining them.

All 120 case executions passed locally. Measurements use a common simulated clock period and do not establish FPGA clock frequency, resource usage, power consumption, or general workload speedup. See [firmware documentation](firmware/README.md) for memory layout, startup behavior, driver return codes, and measurement details.
