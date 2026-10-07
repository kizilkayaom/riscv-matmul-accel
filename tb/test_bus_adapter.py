# Check accelerator address selection and response routing.

import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_bus_adapter(dut):
    
    cases = [
    (0x40000008, 1, 1, 1, 0x08),
    (0x40000000, 1, 1, 1, 0x00),
    (0x400000FF, 1, 1, 1, 0xFF),
    (0x3FFFFFFF, 1, 1, 0, 0xFF),
    (0x40000100, 1, 1, 0, 0x00),
    (0x50000008, 1, 1, 0, 0x08),
    (0x40000008, 0, 1, 1, 0x08),
    (0x40000008, 1, 0, 1, 0x08),
    ]

    for address, valid, wrapper_ready, expected_selected, expected_offset in cases:
        dut.addr.value = address
        dut.valid.value = valid
        dut.wrapper_ready.value = wrapper_ready
        dut.wrapper_rdata.value = 0x12345678

        await Timer(1, unit="ns")

        assert dut.selected.value == expected_selected
        assert dut.offset.value == expected_offset
        assert dut.wrapper_valid.value == (valid and expected_selected)
        assert dut.ready.value == (valid and expected_selected and wrapper_ready)
        assert dut.rdata.value == (0x12345678 if expected_selected else 0)