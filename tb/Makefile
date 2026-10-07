# Build RTL simulations and select cocotb test suites.

SIM = icarus
TOPLEVEL_LANG = verilog
TOPLEVEL = systolicArray
COCOTB_TEST_MODULES = test_array
VERILOG_SOURCES = $(shell pwd)/../rtl/array/pe.v $(shell pwd)/../rtl/array/systolicArray.v $(shell pwd)/../rtl/array/controller.v $(shell pwd)/../rtl/array/register_wrapper.v $(shell pwd)/../rtl/array/bus_adapter.v $(shell pwd)/../rtl/array/accelerator_top.v $(shell pwd)/../rtl/array/picorv32_accelerator.v $(shell pwd)/../rtl/array/simple_ram.v $(shell pwd)/../rtl/soc/memory_system.v

VERILOG_SOURCES += $(shell pwd)/../rtl/vendor/picorv32/picorv32.v $(shell pwd)/../rtl/soc/soc_top.v
export PYTHONPATH := $(abspath ..):$(PYTHONPATH)
export BENCHMARK_CC := $(if $(filter default undefined,$(origin CC)),riscv64-elf-gcc,$(CC))

include $(shell cocotb-config --makefiles)/Makefile.sim

.PHONY: test-soc
test-soc:
	$(MAKE) -C ../firmware
	$(MAKE) sim TOPLEVEL=soc_top COCOTB_TEST_MODULES=test_soc SIM_BUILD=sim_build_soc_matmul COMPILE_ARGS='-Psoc_top.INIT_FILE=\"../firmware/matmul.hex\"'

.PHONY: benchmark-accel
benchmark-accel:
	$(MAKE) -C ../firmware benchmark_accel.hex
	BENCHMARK_VARIANT=accel BENCHMARK_REPORT=../build/benchmark/accel.json BENCHMARK_FIRMWARE=../firmware/benchmark_accel.hex $(MAKE) sim TOPLEVEL=soc_top COCOTB_TEST_MODULES=test_benchmark SIM_BUILD=sim_build_benchmark_accel COMPILE_ARGS='-Psoc_top.INIT_FILE=\"../firmware/benchmark_accel.hex\"'

.PHONY: benchmark-sw
benchmark-sw:
	$(MAKE) -C ../firmware benchmark_sw.hex
	BENCHMARK_VARIANT=sw BENCHMARK_REPORT=../build/benchmark/sw.json BENCHMARK_FIRMWARE=../firmware/benchmark_sw.hex $(MAKE) sim TOPLEVEL=soc_top COCOTB_TEST_MODULES=test_benchmark SIM_BUILD=sim_build_benchmark_sw COMPILE_ARGS='-Psoc_top.INIT_FILE=\"../firmware/benchmark_sw.hex\"'

.PHONY: benchmark-accel-mul benchmark-mul benchmark-c
benchmark-accel-mul:
	$(MAKE) -C ../firmware benchmark_accel.hex
	BENCHMARK_VARIANT=accel_mul BENCHMARK_REPORT=../build/benchmark/accel_mul.json BENCHMARK_FIRMWARE=../firmware/benchmark_accel.hex $(MAKE) sim TOPLEVEL=soc_top COCOTB_TEST_MODULES=test_benchmark SIM_BUILD=sim_build_benchmark_accel_mul COMPILE_ARGS='-Psoc_top.INIT_FILE=\"../firmware/benchmark_accel.hex\" -Psoc_top.ENABLE_MUL=1'

benchmark-mul:
	$(MAKE) -C ../firmware benchmark_mul.hex
	BENCHMARK_VARIANT=mul BENCHMARK_REPORT=../build/benchmark/mul.json BENCHMARK_FIRMWARE=../firmware/benchmark_mul.hex $(MAKE) sim TOPLEVEL=soc_top COCOTB_TEST_MODULES=test_benchmark SIM_BUILD=sim_build_benchmark_mul COMPILE_ARGS='-Psoc_top.INIT_FILE=\"../firmware/benchmark_mul.hex\" -Psoc_top.ENABLE_MUL=1'

benchmark-c:
	$(MAKE) -C ../firmware benchmark_c.hex
	BENCHMARK_VARIANT=c BENCHMARK_REPORT=../build/benchmark/c.json BENCHMARK_FIRMWARE=../firmware/benchmark_c.hex $(MAKE) sim TOPLEVEL=soc_top COCOTB_TEST_MODULES=test_benchmark SIM_BUILD=sim_build_benchmark_c COMPILE_ARGS='-Psoc_top.INIT_FILE=\"../firmware/benchmark_c.hex\"'
