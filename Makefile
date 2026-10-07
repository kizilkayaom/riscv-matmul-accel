# Run regression tests and firmware benchmarks.

.PHONY: test
test:
	python -m unittest discover -s model -p 'test_*.py'
	python -m unittest discover -s tb -p 'test_benchmark_monitor.py'
	python -m unittest discover -s scripts -p 'test_*.py'
	$(MAKE) -C tb TOPLEVEL=processingElement COCOTB_TEST_MODULES=test_pe SIM_BUILD=sim_build_pe
	$(MAKE) -C tb TOPLEVEL=systolicArray COCOTB_TEST_MODULES=test_array SIM_BUILD=sim_build_array
	$(MAKE) -C tb TOPLEVEL=controller COCOTB_TEST_MODULES=test_controller SIM_BUILD=sim_build_controller
	$(MAKE) -C tb TOPLEVEL=register_wrapper COCOTB_TEST_MODULES=test_register_wrapper SIM_BUILD=sim_build_wrapper
	$(MAKE) -C tb TOPLEVEL=bus_adapter COCOTB_TEST_MODULES=test_bus_adapter SIM_BUILD=sim_build_bus_adapter
	$(MAKE) -C tb TOPLEVEL=accelerator_top COCOTB_TEST_MODULES=test_accelerator_top SIM_BUILD=sim_build_accelerator_top
	$(MAKE) -C tb TOPLEVEL=picorv32_accelerator COCOTB_TEST_MODULES=test_picorv32_accelerator SIM_BUILD=sim_build_picorv32_accelerator
	$(MAKE) -C tb TOPLEVEL=simple_ram COCOTB_TEST_MODULES=test_simple_ram SIM_BUILD=sim_build_ram
	$(MAKE) -C tb TOPLEVEL=memory_system COCOTB_TEST_MODULES=test_memory_system SIM_BUILD=sim_build_memory_system
	$(MAKE) -C tb test-soc

.PHONY: benchmark
benchmark:
	python scripts/summarize_benchmarks.py build/benchmark --reset
	$(MAKE) -C tb benchmark-accel
	$(MAKE) -C tb benchmark-sw
	$(MAKE) -C tb benchmark-accel-mul
	$(MAKE) -C tb benchmark-mul
	$(MAKE) -C tb benchmark-c
	python scripts/summarize_benchmarks.py build/benchmark
