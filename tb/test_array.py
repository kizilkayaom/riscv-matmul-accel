# Check array arithmetic, stalls, and reset behavior.

import os
import cocotb
import numpy as np
from cocotb.triggers import Timer
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from model.golden_model import model

A = np.array([[64, -128], [127, 32]], dtype=np.int8)
B = np.array([[64, -64], [127, 32]], dtype=np.int8)


def get_result(dut, r, c, N=2):
    # Extract one row-major result.
    idx = (r * N + c) * 32
    val = (int(dut.out.value) >> idx) & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val

async def run_matrix_case(dut, A, B, case_id="directed", stall_cycles=0, reset_before=True, stall_after=0):
    
    expected, _ = model(A, B)

    if reset_before:
        dut.reset.value = 1
        dut.enable.value = 0
        await RisingEdge(dut.clk)
        dut.reset.value = 0

    # Cycle 0
    dut.enable.value = 1
    dut.a_in.value = (0 & 0xFF) << 8 | (int(A[0,0]) & 0xFF)
    dut.b_in.value = (0 & 0xFF) << 8 | (int(B[0,0]) & 0xFF)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    if stall_cycles > 0 and stall_after == 0:
        await pause_array(dut, stall_cycles, case_id)

    # Cycle 1
    dut.a_in.value = (int(A[1,0]) & 0xFF) << 8 | (int(A[0,1]) & 0xFF)
    dut.b_in.value = (int(B[0,1]) & 0xFF) << 8 | (int(B[1,0]) & 0xFF)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    if stall_cycles > 0 and stall_after == 1:
        await pause_array(dut, stall_cycles, case_id)
    
    # Cycle 2
    dut.a_in.value = (int(A[1,1]) & 0xFF) << 8 | (0 & 0xFF)
    dut.b_in.value = (int(B[1,1]) & 0xFF) << 8 | (0 & 0xFF)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    if stall_cycles > 0 and stall_after == 2:
        await pause_array(dut, stall_cycles, case_id)

    # Drain — zero inputs
    dut.a_in.value = 0
    dut.b_in.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    for r in range(2):
        for c in range(2):
            actual = get_result(dut, r, c)
            assert actual == int(expected[r, c]), (
                f"Case ID: {case_id}\n"
                f"A={A.tolist()}\n"
                f"B={B.tolist()}\n"
                f"C[{r},{c}]: expected {expected[r, c]}, got {actual}"
            )

@cocotb.test()
async def test_array(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    await run_matrix_case(dut, A, B, case_id="mixed signs")
    await run_matrix_case(dut, A, B, case_id="mixed signs with stall", stall_cycles=2)

    A2 = np.array([[1, 2], [3, 4]], dtype=np.int8)
    B2 = np.array([[5, 6], [7, 8]], dtype=np.int8)
    
    await run_matrix_case(dut, A2, B2, case_id="positive operands")

    A3 = np.zeros((2,2), dtype=np.int8)
    B3 = np.array([[1,2], [3,4]], dtype=np.int8)
    
    await run_matrix_case(dut, A3, B3, case_id="zero input")

    A4 = np.full((2,2) , -128, dtype=np.int8)
    B4 = np.full((2,2) , -128, dtype=np.int8)

    await run_matrix_case(dut, A4, B4, case_id="minimum operands")

    A5 = np.full((2,2), -128, dtype=np.int8)
    B5 = np.full((2,2), 127, dtype=np.int8)

    await run_matrix_case(dut, A5, B5, case_id="mixed extremes")

    A6 = np.array([[127, 127], [127, 127]], dtype=np.int8)
    B6 = np.array([[127, 127], [-127, -127]], dtype=np.int8)

    await run_matrix_case(dut, A6, B6, case_id="matrix cancellation")


    seed = int(os.environ.get("TEST_SEED", "42"))
    num_cases = int(os.environ.get("NUM_CASES", "100"))
    rng = np.random.default_rng(seed)

    for i in range(num_cases):
        A_random = rng.integers(-128, 128, size=(2,2), dtype=np.int8)
        B_random = rng.integers(-128, 128, size=(2,2), dtype=np.int8)
        await run_matrix_case(
            dut, A_random, B_random,
            case_id = f"seed={seed}, random case no={i}, uninterrupted run"
        )

        for stall_position in (0, 1, 2):
            for stall_length in (1, 2, 5):
                await run_matrix_case(
                    dut, A_random, B_random,
                    case_id=(
                        f"seed={seed}, case={i}, "
                        f"stall after={stall_position}, length={stall_length}"
                    ),
                    stall_cycles=stall_length,
                    stall_after=stall_position,
                )

    dut._log.info(
        f"Passed 7 directed + {10 * num_cases} random executions. "
        f"There are {num_cases} matrix pairs where each uninterrupted and stalled with lengths 0, 1, 2, and 5. seed={seed}"
    )
        
@cocotb.test()
async def test_interrupt(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # Initial reset
    dut.reset.value = 1
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    # Cycle 0
    dut.enable.value = 1
    dut.a_in.value = (0 & 0xFF) << 8 | (int(A[0,0]) & 0xFF)
    dut.b_in.value = (0 & 0xFF) << 8 | (int(B[0,0]) & 0xFF)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")

    assert dut.out.value != 0

    dut.enable.value = 0
    dut.reset.value = 1
    await Timer(1, unit="ns")
    assert int(dut.out.value) == 0
    dut.reset.value = 0

    A_new = np.array([[1, 2], [3, 4]], dtype=np.int8)
    B_new = np.array([[5, 6], [7, 8]], dtype=np.int8)

    await run_matrix_case(
        dut, A_new, B_new,
        case_id="different matrices after reset",
        reset_before=False,
    )

async def pause_array(dut, stall_cycles, case_id):
    held_output = int(dut.out.value)
    dut.enable.value = 0

    for _ in range(stall_cycles):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.out.value) == held_output, (
            f"{case_id}: accumulators changed while disabled"
        )

    dut.enable.value = 1